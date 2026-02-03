import guardrails.hub

def install_validators():
    print("Installing DetectPromptInjection...")
    try:
        guardrails.hub.install("hub://guardrails/detect_prompt_injection")
        print("Installed DetectPromptInjection")
    except Exception as e:
        print(f"Failed to install DetectPromptInjection: {e}")

    print("Installing UnusualPrompt...")
    try:
        guardrails.hub.install("hub://guardrails/unusual_prompt")
        print("Installed UnusualPrompt")
    except Exception as e:
        print(f"Failed to install UnusualPrompt: {e}")

if __name__ == "__main__":
    install_validators()
