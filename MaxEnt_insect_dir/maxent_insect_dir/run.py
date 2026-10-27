"""CLI entry point for MaxEnt invasive-insect experiments.

One process walks a grid of pathway x feature type x beta x repeat x species x
mixing coefficient ``m``. Each cell fits one MaxEnt model and writes a
timestamped folder of metrics (and, unless skipped, suitability rasters).

The paper performance table (CBI and AUC versus ``m``, 20 repeats) is one
specific slice of that grid, recovered from the May 2025 states on Zeus:

- pathway ``SSP_245`` (the folder name; training climate is WorldClim 1970-2000)
- feature string ``lph`` (linear, hinge, and product)
- beta multiplier 2.0
- ``m`` in {0, 0.25, 0.5, 0.75, 1}
- 10,000 background points, elevation on, cropland off
- species tau from ``config.tau`` (0.5, except root weevil and spongy moth at 0.1)

The later habitat-coverage grid is a different slice: several feature strings,
several betas, and ``m`` fixed at 0.25. The command-line defaults (``lph``,
beta 1.5, ``m`` 0.25) match that habitat grid, not the performance table.
Pass ``--beta-multipliers 2.0`` and the five mixing values to rerun the table.
``--skip-projections`` still writes AUC and CBI; it only skips the GeoTIFFs.
"""

from __future__ import annotations

import argparse
import itertools
import os
import pathlib
from datetime import datetime
from typing import Any, Dict, Iterable, List, Sequence

import geopandas as gpd
import joblib
import numpy as np

from maxent_insect_dir import config, prepare_metadata, run_utils, utils


def create_output_directory(metadata: Dict[str, Any]) -> pathlib.Path:
    """Create a timestamped output directory for one experiment configuration.

    Args:
        metadata: Experiment metadata including pathway, insect, and hyperparameters.

    Returns:
        Path to the created (or existing) output directory.
    """
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    path = pathlib.Path(
        os.path.join(
            config.PATH_TO_SAVE_RESULTS,
            metadata["pathway"],
            metadata["insect_name"],
            str(metadata["bias_uniform_mix_coeff"]),
            metadata["feature_type"],
            str(metadata["beta_multiplier"]),
            (
                f"{metadata['insect_name']}_{metadata['avg']}_{metadata['climate_source']}"
                f"_bias_uniform_max_coeff_{metadata['bias_uniform_mix_coeff']}_{timestamp}"
            ),
        )
    )
    path.mkdir(parents=True, exist_ok=True)
    print(f"Directory {path} ready.")
    return path


def process_presence_background(
    metadata: Dict[str, Any], data: Dict[str, Any]
) -> tuple:
    """Load, thin, and sample presence/background points.

    Args:
        metadata: Experiment metadata.
        data: Prepared raster metadata from ``prepare_experiment_metadata``.

    Returns:
        Tuple of ``(presence, background)`` GeoDataFrames.
    """
    print("Step: get presence-background data...\n")
    return run_utils.get_presence_background(
        insect_name=metadata["insect_name"],
        uniform_raster=data["train"]["bioclim"]["rasters"][0],
        to_thin=metadata["to_thin"],
        bias_uniform_mix_coeff=metadata["bias_uniform_mix_coeff"],
        background_count=metadata["background_count"],
        plot=metadata["plot"],
        save_path=metadata["model_savefig_path"],
        thinning_distance=metadata.get("thinning_distance"),
        kernel_radius=metadata.get("kernel_radius", 160000.0),
        one_per_cell=bool(metadata.get("thin_one_per_cell", False)),
        accessible_area=metadata.get("accessible_area_path"),
    )


def annotate_data(
    metadata: Dict[str, Any],
    presence: gpd.GeoDataFrame,
    background: gpd.GeoDataFrame,
    data: Dict[str, Any],
    raster_labels: Dict[str, List[str]],
) -> tuple:
    """Annotate presence and background points with environmental predictors.

    Args:
        metadata: Experiment metadata.
        presence: Presence points.
        background: Background points.
        data: Raster metadata.
        raster_labels: Labels for bioclim/elevation/crop stacks.

    Returns:
        Annotated ``(presence, background)``.
    """
    print("Step: Annotate bioclim variable...\n")
    presence = run_utils.annotate(
        points=presence,
        rasters=data["train"]["bioclim"]["rasters"],
        labels=raster_labels["bioclim"],
    )
    background = run_utils.annotate(
        points=background,
        rasters=data["train"]["bioclim"]["rasters"],
        labels=raster_labels["bioclim"],
    )

    if metadata["use_elevation"]:
        print("Step: Annotate elevation variable...\n")
        presence = run_utils.annotate(
            points=presence,
            rasters=data["train"]["elevation"]["rasters"],
            labels=raster_labels["elevation"],
        )
        background = run_utils.annotate(
            points=background,
            rasters=data["train"]["elevation"]["rasters"],
            labels=raster_labels["elevation"],
        )

    if metadata["use_crop"]:
        print("Step: Annotate crop information...\n")
        presence = run_utils.annotate(
            points=presence,
            rasters=data["train"]["crop"]["rasters"],
            labels=raster_labels["crop"],
        )
        background = run_utils.annotate(
            points=background,
            rasters=data["train"]["crop"]["rasters"],
            labels=raster_labels["crop"],
        )
    return presence, background


def prepare_test_data(
    metadata: Dict[str, Any], data: Dict[str, Any], raster_labels: Dict[str, List[str]]
) -> gpd.GeoDataFrame:
    """Load held-out background test points and annotate them.

    Args:
        metadata: Experiment metadata.
        data: Raster metadata.
        raster_labels: Predictor labels.

    Returns:
        Annotated test GeoDataFrame.
    """
    test = gpd.read_file(config.PATH_TO_TEST_DATA)[["geometry"]]
    if metadata.get("accessible_area_path"):
        keep = utils.inside_mask(test, metadata["accessible_area_path"])
        print(f"test background inside the accessible area: {int(keep.sum())} of {len(test)}\n")
        test = test.loc[keep].reset_index(drop=True)
    test = run_utils.annotate(
        test, data["train"]["bioclim"]["rasters"], labels=raster_labels["bioclim"], drop_na=True
    )
    if metadata["use_elevation"]:
        test = run_utils.annotate(
            test,
            data["train"]["elevation"]["rasters"],
            labels=["elevation"],
            drop_na=True,
        )
    if metadata["use_crop"]:
        test = run_utils.annotate(
            test, data["train"]["crop"]["rasters"], labels=["crop"], drop_na=True
        )
    return test


def remove_correlated_features(
    metadata: Dict[str, Any],
    presence: gpd.GeoDataFrame,
    background: gpd.GeoDataFrame,
    raster_labels: Dict[str, List[str]],
) -> tuple:
    """Drop highly correlated bioclim predictors and compute KS diagnostics.

    Args:
        metadata: Experiment metadata (updated in place with KS results).
        presence: Annotated presence points.
        background: Annotated background points.
        raster_labels: Predictor labels.

    Returns:
        Tuple ``(metadata, presence, background, cols_to_keep)``.
    """
    cols_to_keep: List[Any] = [metadata["base_cols"]]
    if metadata["use_elevation"]:
        cols_to_keep.append(raster_labels["elevation"])
    if metadata["use_crop"]:
        cols_to_keep.append(raster_labels["crop"])

    if metadata.get("corr_include_elevation") and metadata["use_elevation"]:
        # Elevation joins the |r| filter as one more continuous column. Drop the
        # separate elevation entry added above so it is not listed twice.
        cols_to_keep = [metadata["base_cols"]] + (
            [raster_labels["crop"]] if metadata["use_crop"] else []
        )
        metadata["cols_group_for_uncorrelated_calculations"] = [
            list(raster_labels["elevation"]) + list(metadata["cols_group_for_uncorrelated_calculations"][0])
        ]

    for tag, cols_group in zip(
        ["bioclim"], metadata["cols_group_for_uncorrelated_calculations"]
    ):
        cols_to_keep.append(
            run_utils.remove_correlated_columns(
                presence=presence,
                background=background,
                cols_for_uncorrelated_cal=cols_group,
                threshold=metadata["threshold"],
                plot=metadata["plot"],
                save_path=metadata["model_savefig_path"],
                tag=tag,
            )
        )

    cols_to_keep = list(itertools.chain.from_iterable(cols_to_keep))
    presence = presence[cols_to_keep]
    background = background[cols_to_keep]

    assert list(presence.columns) == list(background.columns) == list(cols_to_keep), (
        "Check the sequence of columns in presence, background, and cols_to_keep"
    )

    metadata["ks_results"] = run_utils.get_ks(
        presence=presence,
        background=background,
        labels=cols_to_keep,
        plot=metadata["plot"],
        save_path=metadata["model_savefig_path"],
    )
    return metadata, presence, background, cols_to_keep


def prepare_train_test_split(
    metadata: Dict[str, Any],
    presence: gpd.GeoDataFrame,
    background: gpd.GeoDataFrame,
    test: gpd.GeoDataFrame,
) -> Dict[str, Any]:
    """Build checkerboard train/test matrices and store them on metadata.

    Args:
        metadata: Experiment metadata.
        presence: Presence points.
        background: Training background points.
        test: Held-out background points.

    Returns:
        Updated metadata dictionary.
    """
    print("Step: prepare test-train data...\n")
    result = run_utils.prepare_test_train(
        presence=presence,
        train_background=background,
        test_background=test,
        plot=metadata["plot"],
        save_path=metadata["model_savefig_path"],
        swap_folds=bool(metadata.get("swap_folds", False)),
    )
    metadata["x_train"] = result["x_train"]
    metadata["y_train"] = result["y_train"]
    metadata["x_test"] = result["x_test"]
    metadata["y_test"] = result["y_test"]
    return metadata


def train_and_evaluate_model(
    metadata: Dict[str, Any], raster_labels: Dict[str, List[str]]
) -> Dict[str, Any]:
    """Fit MaxEnt and compute AUC / Continuous Boyce Index metrics.

    Args:
        metadata: Experiment metadata containing train/test matrices.
        raster_labels: Predictor labels (for categorical indices).

    Returns:
        Updated metadata including model and metrics.
    """
    print("Step: Run the experiment...\n")
    # elapid decides which DataFrame columns are categorical from the pandas
    # dtype ("category"), not from the index list passed to fit(). The 8-bit
    # elevation layer therefore always entered the model as a continuous
    # variable (linear, product and hinge features), in the submitted runs too.
    # Only the cropland code layer is categorical, and only when it is used.
    cat_indices: List[int] = []
    if metadata["use_crop"]:
        col_ = raster_labels["crop"][0]
        for key in ("x_train", "x_test"):
            metadata[key][col_] = metadata[key][col_].astype("category")
        cat_indices.append(metadata["x_train"].columns.get_loc(col_))

    model = run_utils.train_model(
        metadata["x_train"],
        metadata["y_train"],
        cat_indices=cat_indices,
        tau=metadata["tau"],
        beta_multiplier=metadata["beta_multiplier"],
        feature_type=metadata["feature_type"],
    )
    metadata["model"] = model

    print("Step: evaluate the performance metrics...\n")
    feature_importance, auc, cbi_train, cbi_test = run_utils.evaluate(
        model=metadata["model"],
        x_test=metadata["x_test"],
        y_test=metadata["y_test"],
        x_train=metadata["x_train"],
        y_train=metadata["y_train"],
        cat_indices=cat_indices,
        plot=metadata["plot"],
        save_path=metadata["model_savefig_path"],
    )
    metadata["feature_importance"] = feature_importance
    metadata["auc"] = auc
    metadata["cbi_train"] = cbi_train
    metadata["cbi_test"] = cbi_test
    return metadata


def generate_projections(
    metadata: Dict[str, Any], data: Dict[str, Any], raster_labels: Dict[str, List[str]]
) -> None:
    """Write current and future suitability rasters for the fitted model.

    Args:
        metadata: Experiment metadata with a fitted model.
        data: Raster metadata for all time periods.
        raster_labels: Unused; kept for API symmetry with callers.
    """
    del raster_labels  # unused; retained for call-site compatibility
    print("Step: evaluate the future projection...\n")
    all_ranges = {
        "current": "train",
        "2040": "2021_2040",
        "2060": "2041_2060",
        "2080": "2061_2080",
        "2100": "2081_2100",
    }
    wanted = metadata.get("projection_periods") or ["current", "2040", "2060"]
    time_ranges = {k: v for k, v in all_ranges.items() if k in wanted}
    for time, time_range in time_ranges.items():
        rasters = prepare_metadata.prepare_projection_metadata(
            data[time_range], metadata["x_train"].columns
        )
        output_raster = os.path.join(metadata["model_metadata_path"], f"{time}.tif")
        run_utils.compute_projections(
            model=metadata["model"],
            rasters=list(rasters.values()),
            output_raster=output_raster,
            tag=time,
            plot=metadata["plot"],
            save_path=metadata["model_savefig_path"],
        )

    # Fit once, project everywhere: the same fitted model is applied to the
    # future layers of every extra pathway requested with --project-pathways.
    for pathway in metadata.get("project_pathways", []) or []:
        if pathway == metadata["pathway"]:
            continue
        extra, _ = prepare_metadata.prepare_experiment_metadata(
            config.config_worldclim[pathway],
            metadata["avg"],
            use_elevation=metadata["use_elevation"],
            elevation_raster_path=config.PATH_TO_ELEVATION_DATA if metadata["use_elevation"] else None,
            use_crop=metadata["use_crop"],
            crop_raster_path=config.PATH_TO_MOST_GROWN_CROP if metadata["use_crop"] else None,
        )
        for time, time_range in time_ranges.items():
            if time == "current":
                continue
            rasters = prepare_metadata.prepare_projection_metadata(
                extra[time_range], metadata["x_train"].columns
            )
            output_raster = os.path.join(metadata["model_metadata_path"], f"{pathway}_{time}.tif")
            run_utils.compute_projections(
                model=metadata["model"],
                rasters=list(rasters.values()),
                output_raster=output_raster,
                tag=f"{pathway}_{time}",
                plot=False,
                save_path=False,
            )


def save_metadata(metadata: Dict[str, Any]) -> None:
    """Serialize experiment metadata with joblib when enabled.

    Args:
        metadata: Experiment metadata to persist.
    """
    print("Step: store metadata now...\n")
    if metadata["save_experiment_metadata"]:
        joblib.dump(
            metadata, os.path.join(metadata["model_metadata_path"], "experiment_states.pkl")
        )


def run_single_experiment(
    metadata: Dict[str, Any], skip_projections: bool = False
) -> Dict[str, Any]:
    """Execute one full MaxEnt experiment configuration.

    Args:
        metadata: Fully populated experiment metadata dictionary.
        skip_projections: If True, skip writing current/future rasters.

    Returns:
        Completed metadata including model and metrics.
    """
    # Provenance: the code version and command that produced this state.
    try:
        import subprocess, sys
        metadata["git_commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(config.PROJECT_ROOT), capture_output=True, text=True, timeout=10
        ).stdout.strip() or None
        metadata["argv"] = list(sys.argv)
        metadata["git_dirty"] = bool(subprocess.run(
            ["git", "status", "--porcelain", "--", "MaxEnt_insect_dir/maxent_insect_dir"], cwd=str(config.PROJECT_ROOT.parent),
            capture_output=True, text=True, timeout=10).stdout.strip())
    except Exception:  # noqa: BLE001 - provenance is best effort
        metadata["git_commit"] = None
        metadata["argv"] = None

    # Seeded draws: background sampling (numpy) is repeatable when --seed is set.
    if metadata.get("seed") is not None:
        np.random.seed(int(metadata["seed"]))
        print(f"numpy seed set to {metadata['seed']}\n")

    # Paths only at this stage. Raster values are sampled later, at the points.
    # Future SSP periods are listed even when projections are skipped, because
    # the same metadata object feeds both the fit and the optional GeoTIFFs.
    data, raster_labels = prepare_metadata.prepare_experiment_metadata(
        config.config_worldclim[metadata["pathway"]]
        if metadata["climate_source"] == "WorldClim"
        else config.config_CDS["avgs"],
        metadata["avg"],
        use_elevation=metadata["use_elevation"],
        elevation_raster_path=config.PATH_TO_ELEVATION_DATA if metadata["use_elevation"] else None,
        use_crop=metadata["use_crop"],
        crop_raster_path=config.PATH_TO_MOST_GROWN_CROP if metadata["use_crop"] else None,
    )

    # Species-specific cloglog tau. See config.tau. This is not mixing coefficient m.
    metadata["tau"] = config.tau[metadata["insect_name"]]
    metadata["cols_group_for_uncorrelated_calculations"] = [raster_labels["bioclim"]]
    metadata["model_metadata_path"] = create_output_directory(metadata)
    metadata["model_savefig_path"] = metadata["model_metadata_path"]

    # m = bias_uniform_mix_coeff is applied here: fraction of backgrounds drawn
    # from a kernel around presences, remainder drawn uniformly on the raster.
    presence, background = process_presence_background(metadata, data)
    presence, background = annotate_data(metadata, presence, background, data, raster_labels)
    metadata["presence"] = presence
    metadata["background"] = background
    test = prepare_test_data(metadata, data, raster_labels)
    metadata["test"] = test
    metadata, presence, background, cols_to_keep = remove_correlated_features(
        metadata, presence, background, raster_labels
    )
    metadata["cols_to_keep"] = cols_to_keep
    metadata = prepare_train_test_split(metadata, presence, background, test)
    # AUC and CBI are stored on metadata inside this call. The paper table is
    # the mean and sample std of auc["AUC_test"] and cbi_test["Spearman.cor"].
    metadata = train_and_evaluate_model(metadata, raster_labels)
    if skip_projections:
        print("Step: skip projections (metrics only)...\n")
    else:
        generate_projections(metadata, data, raster_labels)
    save_metadata(metadata)
    return metadata


def _parse_floats(values: Sequence[str]) -> List[float]:
    """Parse a list of float strings.

    Args:
        values: String values from argparse.

    Returns:
        List of floats.
    """
    return [float(v) for v in values]


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ``ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        description="Run MaxEnt invasive-insect habitat experiments."
    )
    parser.add_argument(
        "--pathways",
        nargs="+",
        required=True,
        choices=config.VALID_PATHWAYS,
        help="SSP pathways to run (e.g. SSP_245 SSP_370).",
    )
    parser.add_argument(
        "--insects",
        nargs="+",
        default=config.DEFAULT_INSECTS,
        choices=sorted(set(config.Insect_list) - {"Spooted_Lanternfly"}),
        help="Insect keys to model (default: all five paper species).",
    )
    parser.add_argument(
        "--feature-types",
        nargs="+",
        default=config.DEFAULT_FEATURE_TYPES,
        choices=config.FEATURE_TYPES,
        help="MaxEnt feature-type strings (default: lph).",
    )
    parser.add_argument(
        "--beta-multipliers",
        nargs="+",
        type=float,
        default=config.DEFAULT_BETA_MULTIPLIERS,
        help="Regularization multipliers (default: 1.5).",
    )
    parser.add_argument(
        "--bias-mix",
        nargs="+",
        type=float,
        default=config.DEFAULT_BIAS_MIX,
        help="Background bias mixing coefficients m (default: 0.25).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of stochastic repeats per configuration (default: 1).",
    )
    parser.add_argument(
        "--background-count",
        type=int,
        default=10000,
        help="Number of background points (default: 10000).",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Show diagnostic plots during the run.",
    )
    parser.add_argument(
        "--use-crop",
        action="store_true",
        help="Include USDA cropland layer as a categorical predictor.",
    )
    parser.add_argument(
        "--no-elevation",
        action="store_true",
        help="Disable elevation as a predictor.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Tiny run for CI: 1 insect, 1 feature, 1 beta, 500 backgrounds, no projections.",
    )
    parser.add_argument(
        "--skip-projections",
        action="store_true",
        help=(
            "Fit and score the model, but do not write current/future suitability "
            "rasters. Use this for the performance table, which only needs AUC and CBI."
        ),
    )
    parser.add_argument(
        "--project-pathways",
        nargs="+",
        default=None,
        choices=config.VALID_PATHWAYS,
        help=(
            "Also project each fitted model onto the future layers of these pathways "
            "(fit once, project everywhere). Files are named <PATHWAY>_<year>.tif."
        ),
    )
    parser.add_argument(
        "--projection-periods",
        nargs="+",
        default=["current", "2040", "2060"],
        choices=["current", "2040", "2060", "2080", "2100"],
        help="Which suitability rasters to write (default: current 2040 2060).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base numpy seed. Repeat k of a configuration uses seed + k. Default: unseeded.",
    )
    parser.add_argument(
        "--kernel-radius",
        type=float,
        default=160000.0,
        help="Search radius (metres, EPSG:5070) of the presence kernel used for the biased background (default 160000).",
    )
    parser.add_argument(
        "--swap-folds",
        action="store_true",
        help="Exchange the checkerboard colours: train on the usual test cells and test on the usual train cells.",
    )
    parser.add_argument(
        "--corr-include-elevation",
        action="store_true",
        help="Include elevation (a continuous predictor) in the |r| > 0.9 correlation filter.",
    )
    parser.add_argument(
        "--thin-one-per-cell",
        action="store_true",
        help="After distance thinning, keep at most one record per 10 arc-min climate cell.",
    )
    parser.add_argument(
        "--accessible-area",
        default=None,
        help="Name of an accessible-area definition (e.g. eco, eco100, rec200). Background, presences and the "
        "test background are limited to data/data/accessible_area/<insect>_<name>.tif (scripts/accessible_area.py).",
    )
    parser.add_argument(
        "--thin-distance",
        type=float,
        default=None,
        help="Spatial thinning distance in metres for every species (overrides config.spatial_thinning_distance).",
    )
    return parser


def iter_experiment_grid(args: argparse.Namespace) -> Iterable[Dict[str, Any]]:
    """Yield metadata dictionaries for every requested experiment cell.

    Args:
        args: Parsed CLI arguments.

    Yields:
        Metadata dictionaries ready for ``run_single_experiment``.
    """
    insects = args.insects
    feature_types = args.feature_types
    betas = args.beta_multipliers
    bias_mix = args.bias_mix
    repeats = args.repeats
    background_count = args.background_count
    use_elevation = not args.no_elevation
    use_crop = args.use_crop

    if args.smoke_test:
        insects = [insects[0]]
        feature_types = ["l"]
        betas = [1.5]
        bias_mix = [0.25]
        repeats = 1
        background_count = 500

    for pathway in args.pathways:
        for feature_type in feature_types:
            for beta_multiplier in betas:
                for repeat_index in range(repeats):
                    for insect_name in insects:
                        for mix in bias_mix:
                            yield {
                                "repeat_index": repeat_index,
                                "seed": None if args.seed is None else int(args.seed) + repeat_index,
                                "kernel_radius": float(args.kernel_radius),
                                "swap_folds": bool(args.swap_folds),
                                "corr_include_elevation": bool(args.corr_include_elevation),
                                "thinning_distance": args.thin_distance,
                                "thin_one_per_cell": bool(args.thin_one_per_cell),
                                "accessible_area": args.accessible_area,
                                "accessible_area_path": (
                                    str(config.DATA_ROOT / "data" / "accessible_area" / f"{insect_name}_{args.accessible_area}.tif")
                                    if args.accessible_area else None
                                ),
                                "project_pathways": args.project_pathways or [],
                                "projection_periods": list(args.projection_periods),
                                "insect_name": insect_name,
                                "feature_type": feature_type,
                                "beta_multiplier": beta_multiplier,
                                "avg": "1970_2000",
                                "pathway": pathway,
                                "climate_source": "WorldClim",
                                "background_count": background_count,
                                "plot": args.plot,
                                "base_cols": ["geometry"],
                                "threshold": 0.9,
                                "save_experiment_metadata": True,
                                "to_thin": True,
                                "use_elevation": use_elevation,
                                "use_crop": use_crop,
                                "bias_uniform_mix_coeff": mix,
                                "model_savefig_path": None,
                                "model_metadata_path": None,
                                # The performance table is test AUC and test CBI.
                                # Those are computed before any future raster is written.
                                "skip_projections": args.smoke_test or args.skip_projections,
                            }


def main(argv: Sequence[str] | None = None) -> None:
    """Parse CLI arguments and run the experiment grid.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    for metadata in iter_experiment_grid(args):
        skip_projections = bool(metadata.pop("skip_projections", False))
        run_single_experiment(metadata, skip_projections=skip_projections)


if __name__ == "__main__":
    main()
