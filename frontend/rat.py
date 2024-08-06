from app import rat

def create_app():
    """
    Create an instance of the 'rat' application.

    Returns:
        app: An instance of the 'rat' application.
    """
    return rat()

# Create an application instance
app = create_app()

if __name__ == '__main__':
    """
    Entry point of the application.

    Runs the application server if this script is executed directly.
    """
    app.run()
