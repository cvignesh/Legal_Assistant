from guardrails import Guard, Validator, register_validator
from guardrails.validator_base import FailResult

@register_validator(name="test_validator", data_type="string")
class TestValidator(Validator):
    def validate(self, value, metadata):
        return FailResult(error_message="Test Failure")

guard = Guard(name="debug_guard")
guard.use(TestValidator(on_fail="noop"))

try:
    result = guard.validate("test text")
    print("Type of result:", type(result))
    print("Attributes of result:", dir(result))
    
    if hasattr(result, 'validation_passed'):
        print("validation_passed:", result.validation_passed)
    
except Exception as e:
    print("Error during validation/inspection:", e)
