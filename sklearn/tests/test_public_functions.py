from importlib import import_module
from inspect import signature

import pytest

from sklearn.utils._param_validation import generate_invalid_param_val
from sklearn.utils._param_validation import generate_valid_param
from sklearn.utils._param_validation import make_constraint
from sklearn.utils._param_validation import InvalidParameterError


def _get_func_info(func_module):
    module_name, func_name = func_module.rsplit(".", 1)
    module = import_module(module_name)
    func = getattr(module, func_name)

    func_sig = signature(func)
    func_params = [
        p.name
        for p in func_sig.parameters.values()
        if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
    ]

    # The parameters `*args` and `**kwargs` are ignored since we cannot generate
    # constraints.
    required_params = [
        p.name
        for p in func_sig.parameters.values()
        if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
    ]

    return func, func_name, func_params, required_params


def _check_function_param_validation(
    func, func_name, func_params, required_params, parameter_constraints
):
    """Check that an informative error is raised when the value of a parameter does not
    have an appropriate type or value.
    """
    # generate valid values for the required parameters
    valid_required_params = {}
    for param_name in required_params:
        if parameter_constraints[param_name] == "no_validation":
            valid_required_params[param_name] = 1
        else:
            valid_required_params[param_name] = generate_valid_param(
                make_constraint(parameter_constraints[param_name][0])
            )

    # check that there is a constraint for each parameter
    if func_params:
        validation_params = parameter_constraints.keys()
        unexpected_params = set(validation_params) - set(func_params)
        missing_params = set(func_params) - set(validation_params)
        err_msg = (
            "Mismatch between _parameter_constraints and the parameters of"
            f" {func_name}.\nConsider the unexpected parameters {unexpected_params} and"
            f" expected but missing parameters {missing_params}\n"
        )
        assert set(validation_params) == set(func_params), err_msg

    # this object does not have a valid type for sure for all params
    param_with_bad_type = type("BadType", (), {})()

    for param_name in func_params:
        constraints = parameter_constraints[param_name]

        if constraints == "no_validation":
            # This parameter is not validated
            continue

        match = (
            rf"The '{param_name}' parameter of {func_name} must be .* Got .* instead."
        )

        # First, check that the error is raised if param doesn't match any valid type.
        with pytest.raises(InvalidParameterError, match=match):
            func(**{**valid_required_params, param_name: param_with_bad_type})

        # Then, for constraints that are more than a type constraint, check that the
        # error is raised if param does match a valid type but does not match any valid
        # value for this type.
        constraints = [make_constraint(constraint) for constraint in constraints]

        for constraint in constraints:
            try:
                bad_value = generate_invalid_param_val(constraint, constraints)
            except NotImplementedError:
                continue

            with pytest.raises(InvalidParameterError, match=match):
                func(**{**valid_required_params, param_name: bad_value})


PARAM_VALIDATION_FUNCTION_LIST = [
    "sklearn.cluster.cluster_optics_dbscan",
    "sklearn.cluster.compute_optics_graph",
    "sklearn.cluster.estimate_bandwidth",
    "sklearn.cluster.kmeans_plusplus",
    "sklearn.covariance.empirical_covariance",
    "sklearn.covariance.shrunk_covariance",
    "sklearn.datasets.fetch_california_housing",
    "sklearn.datasets.make_sparse_coded_signal",
    "sklearn.decomposition.sparse_encode",
    "sklearn.feature_extraction.grid_to_graph",
    "sklearn.feature_extraction.img_to_graph",
    "sklearn.feature_extraction.image.extract_patches_2d",
    "sklearn.metrics.accuracy_score",
    "sklearn.metrics.auc",
    "sklearn.metrics.cohen_kappa_score",
    "sklearn.metrics.confusion_matrix",
    "sklearn.metrics.det_curve",
    "sklearn.metrics.mean_absolute_error",
    "sklearn.metrics.mean_squared_error",
    "sklearn.metrics.mean_tweedie_deviance",
    "sklearn.metrics.multilabel_confusion_matrix",
    "sklearn.metrics.mutual_info_score",
    "sklearn.metrics.r2_score",
    "sklearn.metrics.roc_curve",
    "sklearn.metrics.zero_one_loss",
    "sklearn.model_selection.train_test_split",
    "sklearn.random_projection.johnson_lindenstrauss_min_dim",
    "sklearn.svm.l1_min_c",
]


@pytest.mark.parametrize("func_module", PARAM_VALIDATION_FUNCTION_LIST)
def test_function_param_validation(func_module):
    """Check param validation for public functions that are not wrappers around
    estimators.
    """
    func, func_name, func_params, required_params = _get_func_info(func_module)

    parameter_constraints = getattr(func, "_skl_parameter_constraints")

    _check_function_param_validation(
        func, func_name, func_params, required_params, parameter_constraints
    )


PARAM_VALIDATION_CLASS_WRAPPER_LIST = [
    ("sklearn.cluster.affinity_propagation", "sklearn.cluster.AffinityPropagation"),
    ("sklearn.covariance.ledoit_wolf", "sklearn.covariance.LedoitWolf"),
    ("sklearn.covariance.oas", "sklearn.covariance.OAS"),
    ("sklearn.decomposition.dict_learning", "sklearn.decomposition.DictionaryLearning"),
    ("sklearn.decomposition.fastica", "sklearn.decomposition.FastICA"),
    ("sklearn.decomposition.non_negative_factorization", "sklearn.decomposition.NMF"),
]


@pytest.mark.parametrize(
    "func_module, class_module", PARAM_VALIDATION_CLASS_WRAPPER_LIST
)
def test_class_wrapper_param_validation(func_module, class_module):
    """Check param validation for public functions that are wrappers around
    estimators.
    """
    func, func_name, func_params, required_params = _get_func_info(func_module)

    module_name, class_name = class_module.rsplit(".", 1)
    module = import_module(module_name)
    klass = getattr(module, class_name)

    parameter_constraints_func = getattr(func, "_skl_parameter_constraints")
    parameter_constraints_class = getattr(klass, "_parameter_constraints")
    parameter_constraints = {
        **parameter_constraints_class,
        **parameter_constraints_func,
    }
    parameter_constraints = {
        k: v for k, v in parameter_constraints.items() if k in func_params
    }

    _check_function_param_validation(
        func, func_name, func_params, required_params, parameter_constraints
    )
