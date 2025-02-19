import importlib.util
import shutil
import os
import ctypes
import logging


def fix_pytorch_libomp():
    """
    Fix PyTorch libomp DLL issue on Windows by copying the correct DLL file if needed.
    """
    torch_spec = importlib.util.find_spec("torch")
    for folder in torch_spec.submodule_search_locations:
        lib_folder = os.path.join(folder, "lib")
        test_file = os.path.join(lib_folder, "fbgemm.dll")
        dest = os.path.join(lib_folder, "libomp140.x86_64.dll")
        if os.path.exists(dest):
            break

        with open(test_file, "rb") as f:
            contents = f.read()
            if b"libomp140.x86_64.dll" not in contents:
                break
        try:
            ctypes.cdll.LoadLibrary(test_file)
        except FileNotFoundError:
            logging.warning("Detected pytorch version with libomp issue, patching.")
            shutil.copyfile(os.path.join(lib_folder, "libiomp5md.dll"), dest)

def fix_pytorch_dml_memory_report():
    """
    Fix PyTorch memory report issue for DML.
    """
    torch_dml_spec = importlib.util.find_spec("torch")
    memory_dll_file = None  # Initialize the variable
  
    if torch_dml_spec is not None:
        for folder in torch_dml_spec.submodule_search_locations:
            lib_folder = os.path.join(folder, "lib")
            test_file = os.path.join(lib_folder, "comfyui_dml_report.dll")
            try:
                print(f"Attempting to load DLL from: {test_file}")
                memory_dll_file = ctypes.cdll.LoadLibrary(test_file)
                break  # Exit the loop if loading is successful  
            except FileNotFoundError:
                logging.warning(f"File not found: {test_file}")
            except OSError as e:
                logging.error(f"Failed to load DLL: {e}")
  
    if memory_dll_file is None:
        logging.error("DLL not found or failed to load. Please ensure the DLL is in the correct location.")
        raise FileNotFoundError("comfyui_dml_report.dll not found or failed to load.")
    else:
        # Check if the function is available
        try:
            memory_dll_file.GetAvailableGpuMemory.restype = ctypes.c_ulonglong
            memory_dll_file.GetAvailableGpuMemory.argtypes = []
        except AttributeError:
            logging.error("GetAvailableGpuMemory function not found in DLL.")
            raise AttributeError("GetAvailableGpuMemory function not found in DLL.")
        try:
            memory_dll_file.GetTotalGpuMemory.restype = ctypes.c_ulonglong
            memory_dll_file.GetTotalGpuMemory.argtypes = []
        except AttributeError:
            logging.error("GetTotalGpuMemory function not found in DLL.")
            raise AttributeError("GetTotalGpuMemory function not found in DLL.")
    return memory_dll_file


