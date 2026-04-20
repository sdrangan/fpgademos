# csynthparse.py:  Module to parse csynth.xml reports from Vivado HLS synthesis

import os
import xml.etree.ElementTree as ET
import pandas as pd

class CsynthParser(object):
    """
    Class for parsing Vivado HLS synthesis reports (csynth.xml).

    Attributes
    ----------
    report_xml : str
        Path to the csynth.xml report file.
    total_resources : dict
        Dictionary of total resources used.
    available_resources : dict
        Dictionary of available resources.
    module_info : dict
        Dictionary mapping module names to their resource usage.
    res_df : pd.DataFrame
        DataFrame summarizing resource usage per module.
    loop_df : pd.DataFrame
        DataFrame containing loop pipeline information.
    """
    def __init__(
            self, 
            sol_path : str | None = None,
            report_path : str | None = None):
        """
        Initialize the CsynthParser with the path to the synthesis report.

        Parameters
        ----------
        sol_path: str:
            Path to the solution directory (e.g., 'sol_1').
            The csynth.xml file is expected to be at
            <sol_path>/syn/report/csynth.xml.
        report_path: str:
            Path to the report directory containing csynth.xml.
            If provided, this takes precedence over sol_path. 
        """

        # Get the location of the report file
        if (report_path is None) and (sol_path is None):
            raise ValueError("Either sol_path or report_path must be provided.")
        if sol_path is not None:
            report_path = os.path.join(sol_path, 'syn', 'report')
          
        self.report_xml = os.path.join(report_path, 'csynth.xml')
        if os.path.exists(self.report_xml) is False:
            raise FileNotFoundError(f"Could not find csynth.xml at {self.report_xml}")

    def get_total_resources(self):
        """
        Parse csynth.xml to extract the total and available resources.

        The results are stored in the instance variables:
        - self.total_resources: dict of total resources
        - self.available_resources: dict of available resources
        """
        tree = ET.parse(self.report_xml)
        root = tree.getroot()

        area_estimates = root.find("AreaEstimates")
        if area_estimates is None:
            raise ValueError("No <AreaEstimates> section found in csynth.xml")

        # Extract Resources
        resources_elem = area_estimates.find("Resources")
        resources = {child.tag: int(child.text) for child in resources_elem}

        # Extract AvailableResources
        avail_elem = area_estimates.find("AvailableResources")
        available_resources = {child.tag: int(child.text) for child in avail_elem}

        self.total_resources = resources
        self.available_resources = available_resources


    def get_module_resources(self):
        """
        Parse csynth.xml to extract resources for each module.
        The results are stored in the instance variable:
        - self.module_info: dict mapping module names to their resource usage.
        """
        tree = ET.parse(self.report_xml)
        root = tree.getroot()

        modules_info = {}
        module_info_elem = root.find("ModuleInformation")
        if module_info_elem is None:
            return modules_info  # no modules present

        for module in module_info_elem.findall("Module"):
            name_elem = module.find("Name")
            if name_elem is None:
                continue
            module_name = name_elem.text.strip()

            resources_elem = module.find("AreaEstimates/Resources")
            if resources_elem is None:
                continue

            # Collect all resource entries (DSP, FF, LUT, etc.)
            resources = {}
            for child in resources_elem:
                # Some values may be "~0" → handle gracefully
                text = child.text.strip()
                try:
                    resources[child.tag] = int(text)
                except ValueError:
                    resources[child.tag] = text  # keep as string if not numeric

            modules_info[module_name] = resources

            self.module_info = modules_info

    @staticmethod
    def _parse_int_or_nan(text):
        if text is None:
            return float("nan")
        try:
            return int(str(text).strip())
        except (TypeError, ValueError):
            return float("nan")

    @classmethod
    def _parse_latency_range(cls, latency_text):
        if latency_text is None:
            return float("nan"), float("nan")

        parts = [part.strip() for part in str(latency_text).split("~")]
        if len(parts) == 2:
            return cls._parse_int_or_nan(parts[0]), cls._parse_int_or_nan(parts[1])

        value = cls._parse_int_or_nan(latency_text)
        return value, value

    def get_loop_pipeline_info(self):
        """
        Parse csynth.xml to get the pipeline initiation interval (II) and depth
        for loops in each module. The results are stored in the instance variable:
        - self.loop_df: pandas DataFrame with loop pipeline information
        """
        tree = ET.parse(self.report_xml)
        root = tree.getroot()

        loop_info = {}
        # Find all ModuleInformation/Module elements
        for module in root.findall(".//ModuleInformation/Module"):
            module_name = module.findtext("Name", default="UnknownModule").strip()

            # Each module may have SummaryOfLoopLatency children
            loop_latency = module.find("PerformanceEstimates/SummaryOfLoopLatency")
            if loop_latency is None:
                continue

            for loop in loop_latency:
                loop_name = loop.findtext("Name", default="UnnamedLoop").strip()
                ii = loop.findtext("PipelineII")
                depth = loop.findtext("PipelineDepth")
                trip_count_min = loop.findtext("TripCount/range/min")
                trip_count_max = loop.findtext("TripCount/range/max")
                latency_min, latency_max = self._parse_latency_range(loop.findtext("Latency"))

                # Convert to int if possible
                try:
                    ii_val = int(ii)
                except (TypeError, ValueError):
                    ii_val = ii
                try:
                    depth_val = int(depth)
                except (TypeError, ValueError):
                    depth_val = depth

                loop_info[f"{module_name}:{loop_name}"] = {
                    "PipelineII": ii_val,
                    "PipelineDepth": depth_val,
                    "TripCountMin": self._parse_int_or_nan(trip_count_min),
                    "TripCountMax": self._parse_int_or_nan(trip_count_max),
                    "LatencyMin": latency_min,
                    "LatencyMax": latency_max,
                }

        # Convert to a pandas DataFrame for easier handling
        self.loop_df = pd.DataFrame.from_dict(loop_info, orient="index")

        nullable_int_columns = [
            "PipelineII",
            "TripCountMin",
            "TripCountMax",
            "LatencyMin",
            "LatencyMax",
        ]
        for column in nullable_int_columns:
            if column in self.loop_df.columns:
                self.loop_df[column] = pd.to_numeric(self.loop_df[column], errors="coerce").astype("Int64")

        if "PipelineDepth" in self.loop_df.columns:
            numeric_depth = pd.to_numeric(self.loop_df["PipelineDepth"], errors="coerce")
            if not numeric_depth.isna().any():
                self.loop_df["PipelineDepth"] = numeric_depth.astype("Int64")

        
    def get_resources(self):
        """
        Create a summary DataFrame of resources for each module as well as the total 
        resources and available resources. 
        """

        # Get the total resources
        self.get_total_resources()

        # Get the module resources
        self.get_module_resources()
  
        # Create the summary DataFrame
        res_types = self.available_resources.keys()
        data = {}
        for mod_name, mod_dict in self.module_info.items():
            m = {}
            for res in res_types:
                if res not in mod_dict:
                    m[res] = 0  # default to 0 if resource type not present
                else:
                    m[res] = mod_dict[res]
            data[mod_name] = m

        data['Total'] = self.total_resources
        data['Available'] = self.available_resources

        if 0:
            data['utilization_%'] = {
                res: (self.total_resources[res] / self.available_resources[res] * 100) 
                if isinstance(self.total_resources[res], int) and isinstance(self.available_resources[res], int) and self.available_resources[res] > 0
                else 'N/A'
                for res in res_types
            }
        self.res_df =  pd.DataFrame.from_dict(data, orient="index")


