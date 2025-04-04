import pandas as pd
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from agno.tools import Toolkit
from agno.utils.log import log_debug, log_info, logger


from agno.tools import Toolkit
from agno.tools.pandas import PandasTools
from agno.utils.log import log_debug, logger


class ExcelTools(Toolkit):
    def __init__(
        self,
        excel_files: Optional[List[Union[str, Path]]] = None,
        base_dir: Union[str, Path] = "data",
        list_files: bool = True,
        convert_to_csv: bool = True,
        get_sheet_names: bool = True,
        **kwargs,
    ):
        super().__init__(name="excel_tools", **kwargs)

        self.excel_files: List[Path] = []
        if excel_files:
            for file in excel_files:
                if isinstance(file, str):
                    self.excel_files.append(Path(file))
                elif isinstance(file, Path):
                    self.excel_files.append(file)
                else:
                    raise ValueError(f"Invalid Excel file: {file}")
        
        # Set base directory
        self.base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
        
        # Create destination directories
        self.input_questions_dir = self.base_dir / "input_questions"
        self.knowledge_dir = self.base_dir / "knowledge"
        
        for directory in [self.input_questions_dir, self.knowledge_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        if list_files:
            self.register(self.list_excel_files)
        if convert_to_csv:
            self.register(self.convert_excel_to_csv)
        if get_sheet_names:
            self.register(self.get_sheet_names)

    def list_excel_files(self) -> str:
        """Returns a list of available Excel files

        Returns:
            str: List of available Excel files
        """
        return json.dumps([str(excel_file) for excel_file in self.excel_files])

    def get_sheet_names(self, excel_file_path: str) -> str:
        """Get the sheet names from an Excel file

        Args:
            excel_file_path (str): The path to the Excel file

        Returns:
            str: JSON string containing sheet names
        """
        try:
            # Convert to Path for consistency
            file_path = Path(excel_file_path)
            
            # Check if file exists
            if not file_path.exists():
                available_files = self.list_excel_files()
                return f"File {excel_file_path} not found. Available files: {available_files}"

            log_info(f"Getting sheet names from file: {file_path}")
            
            # Read the Excel file to get sheet names
            excel = pd.ExcelFile(file_path)
            sheet_names = excel.sheet_names
            
            return json.dumps(sheet_names)
        except Exception as e:
            logger.error(f"Error getting sheet names: {e}")
            return f"Error getting sheet names: {e}"

    def convert_excel_to_csv(
        self, 
        excel_file_path: str, 
        output_type: str = "input_questions",
        sheet_name: Optional[str] = None,
        filename_prefix: Optional[str] = None
    ) -> str:
        """Convert an Excel file to CSV format

        Args:
            excel_file_path (str): The path to the Excel file
            output_type (str): Where to save the CSV file - "input_questions" or "knowledge"
            sheet_name (Optional[str], optional): The sheet name to convert. If None, converts all sheets.
            filename_prefix (Optional[str], optional): Prefix to add to output filenames

        Returns:
            str: Path to the created CSV file(s)
        """
        try:
            # Convert to Path for consistency
            file_path = Path(excel_file_path)
            
            # Check if file exists
            if not file_path.exists():
                available_files = self.list_excel_files()
                return f"File {excel_file_path} not found. Available files: {available_files}"

            log_info(f"Converting Excel file: {file_path}")
            
            # Determine output directory based on specified type
            if output_type.lower() == "input_questions":
                output_dir = self.input_questions_dir
            elif output_type.lower() == "knowledge":
                output_dir = self.knowledge_dir
            else:
                return f"Invalid output_type: {output_type}. Must be 'input_questions' or 'knowledge'."
            
            # Read the Excel file
            excel = pd.ExcelFile(file_path)
            
            # Create prefix for filename
            prefix = ""
            if filename_prefix:
                prefix = f"{filename_prefix}_"
            
            created_files = []
            
            if sheet_name:
                # Check if the sheet exists
                if sheet_name not in excel.sheet_names:
                    sheet_list = json.dumps(excel.sheet_names)
                    return f"Sheet {sheet_name} not found in {file_path}. Available sheets: {sheet_list}"
                
                # Convert specific sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                base_name = file_path.stem
                csv_path = output_dir / f"{prefix}{base_name}_{sheet_name}.csv"
                df.to_csv(csv_path, index=False)
                created_files.append(str(csv_path))
            else:
                # Convert all sheets
                for sheet in excel.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    base_name = file_path.stem
                    csv_path = output_dir / f"{prefix}{base_name}_{sheet}.csv"
                    df.to_csv(csv_path, index=False)
                    created_files.append(str(csv_path))
            
            return json.dumps({
                "status": "success",
                "output_type": output_type,
                "output_directory": str(output_dir),
                "files_created": created_files
            })
        except Exception as e:
            logger.error(f"Error converting Excel to CSV: {e}")
            return f"Error converting Excel to CSV: {e}"


class ExcelProcessorTools(Toolkit):
    def __init__(self, knowledge_folder="knowledge", **kwargs):
        super().__init__(name="excel_processor_tools", **kwargs)
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.knowledge_folder = knowledge_folder
        
        # Create knowledge folder if it doesn't exist
        os.makedirs(self.knowledge_folder, exist_ok=True)
        
        # Register tools
        self.register(self.read_excel_file)
        self.register(self.list_sheets)
        self.register(self.analyze_sheet_columns)
        self.register(self.export_to_csv)
        self.register(self.validate_excel_file)
    
    def validate_excel_file(self, excel_path: str) -> str:
        """
        Validates if the file is a proper Excel file.
        
        :param excel_path: Path to the Excel file
        :return: Validation result
        """
        try:
            if not os.path.exists(excel_path):
                return f"Error: File does not exist: {excel_path}"
            
            if not excel_path.lower().endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
                return f"Error: File does not have an Excel extension: {excel_path}"
            
            # Try to open the file to validate it's a proper Excel file
            try:
                with pd.ExcelFile(excel_path) as _:
                    return f"Valid Excel file: {excel_path}"
            except Exception as e:
                return f"Invalid Excel file: {excel_path}. Error: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error validating Excel file: {e}")
            return f"Error validating Excel file: {e}"
    
    def read_excel_file(self, excel_path: str, chunk_size: int = None) -> str:
        """
        Reads an Excel file and stores each sheet as a separate dataframe.
        
        :param excel_path: Path to the Excel file
        :param chunk_size: Optional chunk size for reading large files in parts
        :return: Success message or error
        """
        try:
            log_debug(f"Reading Excel file: {excel_path}")
            
            # Validate the file
            validation_result = self.validate_excel_file(excel_path)
            if validation_result.startswith("Error") or validation_result.startswith("Invalid"):
                return validation_result
            
            # Get the filename without extension
            base_filename = os.path.basename(excel_path).split('.')[0]
            
            # Read all sheets
            try:
                excel_file = pd.ExcelFile(excel_path, engine=None)  # Let pandas choose the appropriate engine
                sheet_names = excel_file.sheet_names
                
                for sheet_name in sheet_names:
                    df_name = f"{base_filename}_{sheet_name}"
                    
                    try:
                        # If chunk_size is provided, read the file in chunks
                        if chunk_size:
                            chunks = []
                            for chunk in pd.read_excel(excel_file, sheet_name=sheet_name, chunksize=chunk_size):
                                chunks.append(chunk)
                            
                            if chunks:
                                df = pd.concat(chunks, ignore_index=True)
                            else:
                                df = pd.DataFrame()
                        else:
                            df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        
                        if df.empty:
                            log_debug(f"Sheet '{sheet_name}' is empty, skipping")
                            continue
                        
                        # Clean column names (remove whitespace and special characters)
                        df.columns = [str(col).strip() for col in df.columns]
                        
                        self.dataframes[df_name] = df
                        log_debug(f"Loaded sheet '{sheet_name}' as dataframe '{df_name}' with shape {df.shape}")
                    
                    except Exception as sheet_error:
                        logger.error(f"Error reading sheet '{sheet_name}': {sheet_error}")
                        return f"Error reading sheet '{sheet_name}': {sheet_error}"
                
                return f"Successfully read Excel file with {len(sheet_names)} sheets: {', '.join(sheet_names)}"
            
            except pd.errors.EmptyDataError:
                return f"Error: Excel file is empty: {excel_path}"
            except pd.errors.ParserError:
                return f"Error: Excel parsing error, file may be corrupted: {excel_path}"
            except ValueError as ve:
                return f"Error: {str(ve)}"
        
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return f"Error reading Excel file: {e}"
    
    def list_sheets(self) -> str:
        """
        Lists all sheets (dataframes) that have been loaded.
        
        :return: List of loaded dataframes
        """
        if not self.dataframes:
            return "No dataframes loaded. Please read an Excel file first."
        
        result = "Loaded dataframes:\n"
        for df_name, df in self.dataframes.items():
            result += f"- {df_name}: {df.shape[0]} rows × {df.shape[1]} columns\n"
        
        return result
    
    def analyze_sheet_columns(self, dataframe_name: str) -> str:
        """
        Analyzes columns in the specified dataframe to identify relevant ones.
        
        :param dataframe_name: Name of the dataframe to analyze
        :return: Analysis results
        """
        try:
            if dataframe_name not in self.dataframes:
                return f"Error: Dataframe '{dataframe_name}' not found"
            
            df = self.dataframes[dataframe_name]
            
            # Basic column analysis
            column_analysis = {}
            relevant_columns = []
            
            for column in df.columns:
                non_null_count = df[column].count()
                null_percentage = (1 - non_null_count / len(df)) * 100
                unique_values = df[column].nunique()
                
                # Heuristic for relevant columns (customize as needed)
                is_relevant = (
                    null_percentage < 50 and  # Less than 50% nulls
                    unique_values > 1  # More than one unique value
                )
                
                if is_relevant:
                    relevant_columns.append(column)
                
                column_analysis[column] = {
                    "null_percentage": f"{null_percentage:.2f}%",
                    "unique_values": unique_values,
                    "is_relevant": is_relevant
                }
            
            # Create a filtered dataframe with only relevant columns
            filtered_df_name = f"{dataframe_name}_filtered"
            self.dataframes[filtered_df_name] = df[relevant_columns]
            
            # Generate report
            result = f"Column analysis for '{dataframe_name}':\n\n"
            for column, analysis in column_analysis.items():
                relevance = "✓" if analysis["is_relevant"] else "✗"
                result += f"- {column}: {relevance} (Null: {analysis['null_percentage']}, Unique values: {analysis['unique_values']})\n"
            
            result += f"\nCreated filtered dataframe '{filtered_df_name}' with {len(relevant_columns)} relevant columns."
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing columns: {e}")
            return f"Error analyzing columns: {e}"
    
    def export_to_csv(self, dataframe_name: str, filename: Optional[str] = None) -> str:
        """
        Exports the specified dataframe to a CSV file in the knowledge folder.
        
        :param dataframe_name: Name of the dataframe to export
        :param filename: Optional custom filename (without .csv extension)
        :return: Success message or error
        """
        try:
            if dataframe_name not in self.dataframes:
                return f"Error: Dataframe '{dataframe_name}' not found"
            
            df = self.dataframes[dataframe_name]
            
            # Use provided filename or the dataframe name
            output_filename = filename or dataframe_name
            if not output_filename.endswith('.csv'):
                output_filename += '.csv'
            
            output_path = os.path.join(self.knowledge_folder, output_filename)
            
            # Export to CSV
            df.to_csv(output_path, index=False)
            log_debug(f"Exported '{dataframe_name}' to {output_path}")
            
            return f"Successfully exported '{dataframe_name}' to {output_path}"
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return f"Error exporting to CSV: {e}"
