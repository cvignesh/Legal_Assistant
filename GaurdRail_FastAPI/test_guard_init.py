from guardrails import Guard, Validator, register_validator
from guardrails.validator_base import PassResult

@register_validator(name="test_validator", data_type="string")
class TestValidator(Validator):
    def validate(self, value, metadata):
        return PassResult()

try:
    v = TestValidator()
    print("Validator created:", v)
    
    # Attempt 1: Constructor
    try:
        g = Guard(name="test", validators=[v])
        print("Success: Guard(validators=[v])")
    except Exception as e:
        print("Failed: Guard(validators=[v]) ->", e)

    # Attempt 2: Use
    try:
        g = Guard(name="test")
        g.use(v)
        print("Success: Guard().use(v)")
    except Exception as e:
        print("Failed: Guard().use(v) ->", e)

except Exception as e:
    print("General Error:", e)
