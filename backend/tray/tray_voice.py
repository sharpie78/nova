def toggle_voice(enable_voice_action, icons):
    if enable_voice_action.text() == f"{icons['voice']} Enable Voice":
        enable_voice_action.setText(f"{icons['quit']} Disable Voice")
        print("Voice Enabled")
    else:
        enable_voice_action.setText(f"{icons['voice']} Enable Voice")
        print("Voice Disabled")
