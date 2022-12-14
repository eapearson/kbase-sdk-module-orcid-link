from orcidlink.service_clients.ServiceClientBase import ServiceClientBase


class ServiceWizard(ServiceClientBase):
    module = "ServiceWizard"

    def get_service_status(self, module_name: str, version: str | None = None):
        if version not in ["dev", "beta", "release", None]:
            raise TypeError("module version must be one of 'dev', 'beta', 'release', or None")
        return self.call_func(
            "get_service_status",
            {
                "module_name": module_name,
                "version": version
            },
        )

    def status(self):
        return self.call_func(
            "status"
        )
