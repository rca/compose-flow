"""Define checks to be run against Kubernetes YAML"""

from abc import ABC
import logging
from typing import List

import yaml

from pdb import set_trace as bp

class BaseChecker(ABC):
    check_prefix = None

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def check(self, rendered: str) -> List[str]:
        """Main method that runs all check methods defined on this class."""
        errors = []

        if self.check_prefix is None:
            raise AttributeError("The class attribute `check_prefix` must be non-null!")

        # Load all YAML documents from string `rendered`
        loaded = self._load_rendered_yaml(rendered)

        checks = self._get_all_checks()
        for check in checks:
            result = check(loaded)
            if result:
                errors.append(result)

        return errors

    def _get_all_checks(self):
        """Return a list of the methods on this class which begin with `check_prefix`."""
        this_class = self.__class__

        check_list = [
            getattr(self, func) for func in dir(self.__class__)
            if callable(getattr(this_class, func))
            and func.startswith(self.check_prefix)
        ]

        return check_list

    def _load_rendered_yaml(self, rendered: str) -> dict:
        """Load the rendered YAML which is passed in to the `check` method."""
        return yaml.load_all(rendered)


class ManifestChecker(BaseChecker):
    """Check Kubernetes YAML resource manifests."""
    check_prefix = '_check_manifest_'

    def _check_manifest_ingress_annotations(self, documents: list) -> str:
        """Check ingresses for appropriate annotations"""
        ingress_kind = 'Ingress'
        internal_value = 'internal'
        external_value = 'internet-facing'

        missing_metadata_msg = ('Ingress resources MUST specify a metadata section including'
                                'name, namespace, and appropriate annotations!')
        ingress_error_msg = ('Ingress resources MUST specify a scheme annotation to avoid '
                             'unintentionally exposing a service to the public Internet!')

        public_ingress_warning = ('An ingress resource in this deployment is internet-facing!\n\n'
                                  'Please ensure you are deploying to a production cluster '
                                  'and you intend to make your services PUBLICLY accessible!')

        for doc in documents:
            if doc.get('kind') == ingress_kind:
                metadata = doc.get('metadata')
                if metadata is None:
                    return missing_metadata_msg
                annotations = metadata.get('annotations')
                if annotations is None:
                    return ingress_error_msg

                class_anno = annotations.get('kubernetes.io/ingress.class')
                if class_anno != 'nginx':
                    print(annotations)
                    has_internal = any('scheme' in k and internal_value in v for k, v in annotations.items())
                    has_external = any('scheme' in k and external_value in v for k, v in annotations.items())
                    if has_external:
                        self.logger.warn(public_ingress_warning)
                    if not has_internal and not has_external:
                        return ingress_error_msg


class AnswersChecker(BaseChecker):
    check_prefix = '_check_answers_'
