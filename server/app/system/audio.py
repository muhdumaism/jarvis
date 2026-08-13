import sys
import ctypes
import structlog

logger = structlog.get_logger("jarvis.system.audio")

# Define Windows specific structures if running on Windows
IS_WINDOWS = sys.platform == "win32"

def get_windows_audio_devices():
    """List all active audio output devices on Windows."""
    if not IS_WINDOWS:
        return []

    try:
        from pycaw.pycaw import AudioUtilities, EDataFlow
        from pycaw.api.mmdeviceapi.depend.structures import PROPERTYKEY
        from comtypes import GUID
        
        device_list = []
        device_enumerator = AudioUtilities.GetDeviceEnumerator()
        endpoints = device_enumerator.EnumAudioEndpoints(EDataFlow.eRender.value, 0x1) # DEVICE_STATE_ACTIVE
        
        for i in range(endpoints.GetCount()):
            try:
                device = endpoints.Item(i)
                device_id = device.GetId()
                store = device.OpenPropertyStore(0) # STGM_READ
                
                key = PROPERTYKEY()
                key.fmtid = GUID("{a45c254e-df1c-4efd-8020-67d146a850e0}")
                key.pid = 14
                
                prop = store.GetValue(ctypes.byref(key))
                friendly_name = prop.union.pwszVal
                
                device_list.append({
                    "id": device_id,
                    "name": friendly_name
                })
            except Exception as ex:
                logger.debug("windows.audio.device_fetch_error", index=i, error=str(ex))
                
        return device_list
    except Exception as e:
        logger.error("windows.audio.failed_to_list_devices", error=str(e))
        return []

def is_bluetooth_speaker_connected(speaker_name: str) -> bool:
    """Check if the specified Bluetooth speaker is connected and active as an audio output."""
    if not IS_WINDOWS:
        return True # Fallback for non-Windows platforms
        
    if not speaker_name:
        return False
        
    devices = get_windows_audio_devices()
    speaker_name_lower = speaker_name.lower()
    
    for dev in devices:
        if speaker_name_lower in dev["name"].lower():
            return True
            
    return False

def get_current_audio_output() -> str:
    """Get the friendly name of the current default audio output device."""
    if not IS_WINDOWS:
        return "System Default Audio Output"
        
    try:
        from pycaw.pycaw import AudioUtilities, EDataFlow, ERole
        from pycaw.api.mmdeviceapi.depend.structures import PROPERTYKEY
        from comtypes import GUID
        
        device_enumerator = AudioUtilities.GetDeviceEnumerator()
        default_device = device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eConsole.value)
        
        store = default_device.OpenPropertyStore(0)
        key = PROPERTYKEY()
        key.fmtid = GUID("{a45c254e-df1c-4efd-8020-67d146a850e0}")
        key.pid = 14
        
        prop = store.GetValue(ctypes.byref(key))
        return prop.union.pwszVal or "Unknown Audio Device"
    except Exception as e:
        logger.debug("windows.audio.failed_to_get_default", error=str(e))
        return "Unknown Audio Device"
