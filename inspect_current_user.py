import jwt
import sys

def decode_jwt(token_str):
    # Note: This does not verify the signature - it just decodes the token
    # You'd need the same SECRET_KEY from your auth service to properly verify
    try:
        # Split the token and get the payload part (second segment)
        parts = token_str.split('.')
        if len(parts) != 3:
            print("Invalid JWT format - should have 3 parts")
            return None
            
        # Decode the payload without verification
        decoded = jwt.decode(token_str, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        token = sys.argv[1]
        decoded = decode_jwt(token)
        if decoded:
            print("\nDecoded JWT Token:")
            for key, value in decoded.items():
                print(f"{key}: {value}")
    else:
        print("Please provide a JWT token as argument") 