from abc import ABC, abstractmethod
import os
from typing import Any, List, Optional, Union

import numpy as np
import pandas as pd
from PIL import Image


from detectionmetrics.datasets import dataset as dm_dataset
import detectionmetrics.utils.conversion as uc
import detectionmetrics.utils.io as uio


class PerceptionModel(ABC):
    """Base class for all vision perception models (e.g., segmentation, detection).

    :param model: Model object
    :type model: Any
    :param model_type: Model type (e.g. scripted, compiled, etc.)
    :type model_type: str
    :param model_cfg: JSON file containing model configuration
    :type model_cfg: str
    :param ontology_fname: JSON file containing model output ontology
    :type ontology_fname: str
    :param model_fname: Model file or directory, defaults to None
    :type model_fname: Optional[str], optional
    """

    def __init__(
        self,
        model: Any,
        model_type: str,
        model_cfg: str,
        ontology_fname: str,
        model_fname: Optional[str] = None,
    ):
        self.model = model
        self.model_type = model_type
        self.model_fname = model_fname

        # Check that provided paths exist
        assert os.path.isfile(ontology_fname), "Ontology file not found"
        assert os.path.isfile(model_cfg), "Model configuration not found"
        if self.model_fname is not None:
            assert os.path.exists(model_fname), "Model file or directory not found"

        # Read ontology and model configuration
        self.ontology = uio.read_json(ontology_fname)
        self.model_cfg = uio.read_json(model_cfg)
        self.n_classes = len(self.ontology)

    @abstractmethod
    def inference(
        self, data: Union[np.ndarray, Image.Image]
    ) -> Union[np.ndarray, Image.Image, dict]:
        """Perform inference for a single image or point cloud."""
        raise NotImplementedError

    @abstractmethod
    def eval(self, *args, **kwargs) -> pd.DataFrame:
        """Evaluate the model on the given dataset."""
        raise NotImplementedError

    @abstractmethod
    def get_computational_cost(self, runs: int = 30, warm_up_runs: int = 5) -> dict:
        """Get different metrics related to the computational cost of the model

        :param runs: Number of runs to measure inference time, defaults to 30
        :type runs: int, optional
        :param warm_up_runs: Number of warm-up runs, defaults to 5
        :type warm_up_runs: int, optional
        :return: Dictionary containing computational cost information
        """
        raise NotImplementedError

    def get_lut_ontology(
        self, dataset_ontology: dict, ontology_translation: Optional[str] = None
    ):
        """Build ontology lookup table (leave empty if ontologies match)

        :param dataset_ontology: Image or LiDAR dataset ontology
        :type dataset_ontology: dict
        :param ontology_translation: JSON file containing translation between model and dataset ontologies, defaults to None
        :type ontology_translation: Optional[str], optional
        """
        lut_ontology = None
        if dataset_ontology != self.ontology:
            if ontology_translation is not None:
                ontology_translation = uio.read_json(ontology_translation)
            lut_ontology = uc.get_ontology_conversion_lut(
                dataset_ontology,
                self.ontology,
                ontology_translation,
                self.model_cfg.get("ignored_classes", []),
            )
        return lut_ontology


class SegmentationModel(PerceptionModel):
    """Parent segmentation model class

    :param model: Segmentation model object
    :type model: Any
    :param model_type: Model type (e.g. scripted, compiled, etc.)
    :type model_type: str
    :param model_cfg: JSON file containing model configuration
    :type model_cfg: str
    :param ontology_fname: JSON file containing model output ontology
    :type ontology_fname: str
    :param model_fname: Model file or directory, defaults to None
    :type model_fname: Optional[str], optional
    """

    def __init__(
        self,
        model: Any,
        model_type: str,
        model_cfg: str,
        ontology_fname: str,
        model_fname: Optional[str] = None,
    ):
        super().__init__(model, model_type, model_cfg, ontology_fname, model_fname)

    @abstractmethod
    def inference(
        self, points: Union[np.ndarray, Image.Image]
    ) -> Union[np.ndarray, Image.Image]:
        """Perform inference for a single image or point cloud

        :param image: Either a numpy array (LiDAR point cloud) or a PIL image
        :type image: Union[np.ndarray, Image.Image]
        :return: Segmenation result as a point cloud or image with label indices
        :rtype: Union[np.ndarray, Image.Image]
        """
        raise NotImplementedError

    @abstractmethod
    def eval(
        self,
        dataset: dm_dataset.SegmentationDataset,
        split: str | List[str] = "test",
        ontology_translation: Optional[str] = None,
        predictions_outdir: Optional[str] = None,
        results_per_sample: bool = False,
    ) -> pd.DataFrame:
        """Perform evaluation for an image segmentation dataset

        :param dataset: Segmentation dataset for which the evaluation will be performed
        :type dataset: ImageSegmentationDataset
        :param split: Split or splits to be used from the dataset, defaults to "test"
        :type split: str | List[str], optional
        :param ontology_translation: JSON file containing translation between dataset and model output ontologies
        :type ontology_translation: str, optional
        :param predictions_outdir: Directory to save predictions per sample, defaults to None. If None, predictions are not saved.
        :type predictions_outdir: Optional[str], optional
        :param results_per_sample: Whether to store results per sample or not, defaults to False. If True, predictions_outdir must be provided.
        :type results_per_sample: bool, optional
        :return: DataFrame containing evaluation results
        :rtype: pd.DataFrame
        """
        raise NotImplementedError


class ImageSegmentationModel(SegmentationModel):
    """Parent image segmentation model class

    :param model: Image segmentation model object
    :type model: Any
    :param model_type: Model type (e.g. scripted, compiled, etc.)
    :type model_type: str
    :param model_cfg: JSON file containing model configuration (e.g. image size or normalization parameters)
    :type model_cfg: str
    :param ontology_fname: JSON file containing model output ontology
    :type ontology_fname: str
    :param model_fname: Model file or directory
    :type model_fname: Optional[str], optional
    """

    def __init__(
        self,
        model: Any,
        model_type: str,
        model_cfg: str,
        ontology_fname: str,
        model_fname: Optional[str] = None,
    ):
        super().__init__(model, model_type, model_cfg, ontology_fname, model_fname)

    @abstractmethod
    def inference(self, image: Image.Image) -> Image.Image:
        """Perform inference for a single image

        :param image: PIL image.
        :type image: Image.Image
        :return: Segmenation result as PIL image
        :rtype: Image.Image
        """
        raise NotImplementedError

    @abstractmethod
    def eval(
        self,
        dataset: dm_dataset.ImageSegmentationDataset,
        split: str | List[str] = "test",
        ontology_translation: Optional[str] = None,
        predictions_outdir: Optional[str] = None,
        results_per_sample: bool = False,
    ) -> pd.DataFrame:
        """Perform evaluation for an image segmentation dataset

        :param dataset: Image segmentation dataset for which the evaluation will be performed
        :type dataset: ImageSegmentationDataset
        :param split: Split or splits to be used from the dataset, defaults to "test"
        :type split: str | List[str], optional
        :param ontology_translation: JSON file containing translation between dataset and model output ontologies
        :type ontology_translation: str, optional
        :param predictions_outdir: Directory to save predictions per sample, defaults to None. If None, predictions are not saved.
        :type predictions_outdir: Optional[str], optional
        :param results_per_sample: Whether to store results per sample or not, defaults to False. If True, predictions_outdir must be provided.
        :type results_per_sample: bool, optional
        :return: DataFrame containing evaluation results
        :rtype: pd.DataFrame
        """
        raise NotImplementedError


class LiDARSegmentationModel(SegmentationModel):
    """Parent LiDAR segmentation model class

    :param model: LiDAR segmentation model object
    :type model: Any
    :param model_type: Model type (e.g. scripted, compiled, etc.)
    :type model_type: str
    :param model_cfg: JSON file containing model configuration (e.g. sampling method, input format, etc.)
    :type model_cfg: str
    :param ontology_fname: JSON file containing model output ontology
    :type ontology_fname: str
    :param model_fname: Model file or directory
    :type model_fname: Optional[str], optional
    """

    def __init__(
        self,
        model: Any,
        model_type: str,
        model_cfg: str,
        ontology_fname: str,
        model_fname: Optional[str] = None,
    ):
        super().__init__(model, model_type, model_cfg, ontology_fname, model_fname)

    @abstractmethod
    def inference(self, points: np.ndarray) -> np.ndarray:
        """Perform inference for a single image

        :param image: Point cloud xyz array
        :type image: np.ndarray
        :return: Segmenation result as a point cloud with label indices
        :rtype: np.ndarray
        """
        raise NotImplementedError

    @abstractmethod
    def eval(
        self,
        dataset: dm_dataset.LiDARSegmentationDataset,
        split: str | List[str] = "test",
        ontology_translation: Optional[str] = None,
        predictions_outdir: Optional[str] = None,
        results_per_sample: bool = False,
    ) -> pd.DataFrame:
        """Perform evaluation for a LiDAR segmentation dataset

        :param dataset: LiDAR segmentation dataset for which the evaluation will be performed
        :type dataset: LiDARSegmentationDataset
        :param split: Split or splits to be used from the dataset, defaults to "test"
        :type split: str | List[str], optional
        :param ontology_translation: JSON file containing translation between dataset and model output ontologies
        :type ontology_translation: str, optional
        :param predictions_outdir: Directory to save predictions per sample, defaults to None. If None, predictions are not saved.
        :type predictions_outdir: Optional[str], optional
        :param results_per_sample: Whether to store results per sample or not, defaults to False. If True, predictions_outdir must be provided.
        :type results_per_sample: bool, optional
        :return: DataFrame containing evaluation results
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

class DetectionModel(PerceptionModel):
    """Parent detection model class

    :param model: Detection model object
    :type model: Any
    :param model_type: Model type (e.g. scripted, compiled, etc.)
    :type model_type: str
    :param model_cfg: JSON file containing model configuration
    :type model_cfg: str
    :param ontology_fname: JSON file containing model output ontology
    :type ontology_fname: str
    :param model_fname: Model file or directory, defaults to None
    :type model_fname: Optional[str], optional
    """

    def __init__(
        self,
        model: Any,
        model_type: str,
        model_cfg: str,
        ontology_fname: str,
        model_fname: Optional[str] = None,
    ):
        super().__init__(model, model_type, model_cfg, ontology_fname, model_fname)

    @abstractmethod
    def inference(
        self, data: Union[np.ndarray, Image.Image]
    ) -> List[dict]:
        """Perform inference for a single input (image or point cloud)

        :param data: Input image or LiDAR point cloud
        :type data: Union[np.ndarray, Image.Image]
        :return: List of detection results (each a dict with bbox, confidence, class)
        :rtype: List[dict]
        """
        raise NotImplementedError

    @abstractmethod
    def eval(
        self,
        dataset: dm_dataset.DetectionDataset,
        split: Union[str, List[str]] = "test",
        ontology_translation: Optional[str] = None,
        predictions_outdir: Optional[str] = None,
        results_per_sample: bool = False,
    ) -> pd.DataFrame:
        """Perform evaluation for a detection dataset

        :param dataset: Detection dataset for which evaluation will be performed
        :type dataset: ImageDetecctionDataset
        :param split: Split(s) to use, defaults to "test"
        :type split: Union[str, List[str]]
        :param ontology_translation: JSON file containing translation between dataset and model output ontologies
        :type ontology_translation: Optional[str]
        :param predictions_outdir: Directory to save predictions per sample, defaults to None. If None, predictions are not saved.
        :type predictions_outdir: Optional[str]
        :param results_per_sample: Whether to store results per sample or not, defaults to False. If True, predictions_outdir must be provided.
        :type results_per_sample: bool
        :return: DataFrame containing evaluation metrics
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

class ImageDetectionModel(DetectionModel):
    """Parent image detection model class

    :param model: Detection model object
    :type model: Any
    :param model_type: Model type (e.g. scripted, compiled, etc.)
    :type model_type: str
    :param model_cfg: JSON file containing model configuration (e.g. image size or normalization parameters)
    :type model_cfg: str
    :param ontology_fname: JSON file containing model output ontology
    :type ontology_fname: str
    :param model_fname: Model file or directory, defaults to None
    :type model_fname: Optional[str], optional
    """

    def __init__(
        self,
        model: Any,
        model_type: str,
        model_cfg: str,
        ontology_fname: str,
        model_fname: Optional[str] = None,
    ):
        super().__init__(model, model_type, model_cfg, ontology_fname, model_fname)

    @abstractmethod
    def inference(self, image: Image.Image) -> List[dict]:
        """Perform inference for a single image

        :param image: PIL image
        :type image: Image.Image
        :return: List of detection results
        :rtype: List[dict]
        """
        raise NotImplementedError

    @abstractmethod
    def eval(
        self,
        dataset: dm_dataset.ImageDetectionDataset,
        split: Union[str, List[str]] = "test",
        ontology_translation: Optional[str] = None,
        predictions_outdir: Optional[str] = None,
        results_per_sample: bool = False,
    ) -> pd.DataFrame:
        """Evaluate the image detection model

        :param dataset: Image detection dataset for which the evaluation will be performed
        :type dataset: ImageDetectionDataset
        :param split: Split(s) to use, defaults to "test"
        :type split: Union[str, List[str]]
        :param ontology_translation: JSON file containing translation between dataset and model output ontologies
        :type ontology_translation: Optional[str]
        :param predictions_outdir: Directory to save predictions per sample, defaults to None. If None, predictions are not saved.
        :type predictions_outdir: Optional[str]
        :param results_per_sample: Whether to store results per sample or not, defaults to False. If True, predictions_outdir must be provided.
        :type results_per_sample: bool
        :return: DataFrame containing evaluation metrics
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

class LiDARDetectionModel(DetectionModel):
    """Parent LiDAR detection model class

    :param model: Detection model object
    :type model: Any
    :param model_type: Model type (e.g. scripted, compiled, etc.)
    :type model_type: str
    :param model_cfg: JSON file with model configuration
    :type model_cfg: str
    :param ontology_fname: JSON file containing model output ontology
    :type ontology_fname: str
    :param model_fname: Model file or directory, defaults to None
    :type model_fname: Optional[str], optional
    """

    def __init__(
        self,
        model: Any,
        model_type: str,
        model_cfg: str,
        ontology_fname: str,
        model_fname: Optional[str] = None,
    ):
        super().__init__(model, model_type, model_cfg, ontology_fname, model_fname)

    @abstractmethod
    def inference(self, points: np.ndarray) -> List[dict]:
        """Perform inference for a single LiDAR point cloud

        :param points: N x 3 or N x 4 point cloud array
        :type points: np.ndarray
        :return: List of detection results
        :rtype: List[dict]
        """
        raise NotImplementedError

    @abstractmethod
    def eval(
        self,
        dataset: dm_dataset.LiDARDetectionDataset,
        split: Union[str, List[str]] = "test",
        ontology_translation: Optional[str] = None,
        predictions_outdir: Optional[str] = None,
        results_per_sample: bool = False,
    ) -> pd.DataFrame:
        """Perform evaluation for a LiDAR detection dataset

        :param dataset: LiDAR detection dataset for which the evaluation will be performed
        :type dataset: LiDARDetectionDataset
        :param split: Split or splits to be used from the dataset, defaults to "test"
        :type split: Union[str, List[str]]
        :param ontology_translation: JSON file containing translation between dataset and model output ontologies
        :type ontology_translation: Optional[str]
        :param predictions_outdir: Directory to save predictions per sample, defaults to None. If None, predictions are not saved.
        :type predictions_outdir: Optional[str]
        :param results_per_sample: Whether to store results per sample or not, defaults to False. If True, predictions_outdir must be provided.
        :type results_per_sample: bool, optional
        :return: DataFrame containing evaluation metrics
        :rtype: pd.DataFrame
        """
        raise NotImplementedError