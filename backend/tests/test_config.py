from app.core.config import Settings


def test_cors_origins_accept_comma_separated_environment_style_value():
    configured = Settings(cors_origins="http://localhost:3000, https://ops.example.com")
    assert configured.cors_origins == [
        "http://localhost:3000",
        "https://ops.example.com",
    ]
