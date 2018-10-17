"""Define checks to be run against Kubernetes YAML"""

from abc import ABC
import logging
from typing import List


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

        checks = self._get_all_checks()
        for check in checks:
            result = check(rendered)
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


class ManifestChecker(BaseChecker):
    """Check Kubernetes YAML resource manifests."""
    check_prefix = '_check_manifest_'

    def _check_manifest_ingress_annotations(self, rendered: str) -> str:
        """Check ingresses for appropriate annotations"""
        kind = 'Ingress'
        nginx_annotation = 'kubernetes.io/ingress.class: nginx'
        internal_annotation = 'scheme: internal'
        external_annotation = 'scheme: internet-facing'

        if f'kind: {kind}' in rendered:
            if nginx_annotation not in rendered:
                has_internal = internal_annotation in rendered
                has_external = external_annotation in rendered

                if has_external:
                    self.logger.warn('An ingress resource in this deployment is internet-facing!\n'
                                     'Please ensure you are deploying to a production cluster '
                                     'and you intend to make your services publicly accessible!')
                if not has_internal and not has_external:
                    return ('Ingress resources MUST specify a scheme to avoid '
                            'unintentionally exposing a service to the public Internet!')


class AnswersChecker(BaseChecker):
    check_prefix = '_check_answers_'
