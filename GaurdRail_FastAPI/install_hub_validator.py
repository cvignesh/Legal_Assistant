try:
    import guardrails.hub
    print("guardrails.hub imported")
    if hasattr(guardrails.hub, 'install'):
        print("Found install function")
        try:
            guardrails.hub.install("hub://guardrails/detect_pii")
            print("Installation successful")
        except Exception as e:
            print(f"Installation failed: {e}")
    else:
        print("No install function in guardrails.hub")
        print("Attributes:", dir(guardrails.hub))

except ImportError:
    print("Could not import guardrails.hub")
