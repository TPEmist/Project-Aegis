import os
from hatchling.metadata.plugin.interface import MetadataHookInterface


class CustomMetadataHook(MetadataHookInterface):
    PLUGIN_NAME = "custom"

    def update(self, metadata):
        if not os.path.exists("README.pypi.md"):
            import runpy
            runpy.run_path("scripts/build_pypi_readme.py")

        with open("README.pypi.md", encoding="utf-8") as f:
            metadata["readme"] = {
                "content-type": "text/markdown",
                "text": f.read(),
            }
