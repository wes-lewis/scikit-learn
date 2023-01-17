"""
The :mod:`sklearn.mixture` module implements mixture modeling algorithms.
"""

from ._gaussian_mixture import GaussianMixture
from ._bayesian_mixture import BayesianGaussianMixture
from ._weighted_mixture import WeightedGaussianMixture
from ._weighted_mixture_efficient import WeightedGaussianMixtureEfficient
from ._weighted_mixture_changed import WeightedGaussianMixtureChanged


__all__ = ["GaussianMixture", "BayesianGaussianMixture", "WeightedGaussianMixture","WeightedGaussianMixtureEfficient","WeightedGaussianMixtureChanged"]
