# Item Catalog Application
This application provides a list of items within a variety of categories as well as provides a user registration and authentication system. Registered users will have the ability to add, edit and delete their own items.

## Run
In order for the application to run successfully, the user must first register this application with Google in order to use the OAuth2 login feature and add `http://localhost:5000` to the authorized JavaScript origins and `http://localhost:5000/login` and `http://localhost:5000/oauth/google` to the authorized redirect URIs. Then, the user must dowload the client secrets and store them in a `client_secrets.json` file, in the same directory as `application.py`.
Next, the usr must run `database_setup.py`, followed by `catalog.py`. These files create the database and tables and populate them with the categories and several items. 
Lastly, execute `application.py` to launch the program, and navigate to `http://localhost:500` to peruse the app.

## Files
#### database_setup.py
This file creates the `User`, `Category`, and `Item` tables. Both `Category` and `Item` have a decorator to return the table data in an easily serializable format.

#### catalog.py
This file prepopulates the SQLite database with the categories and multiple items. Additional items can be created through the user login system.

#### application.py
This file handles all the backend of the web application, and is built using the Python framework Flask. Many of the functions use the `route()` decorator to bind the functions to URLs. The application uses Flask's `session` object to handle user sessions as well as authorization to ensure only authorized (registered) users can add, edit, and delete their own items.
Additionally, JSON endpoints are provided for the entire catalog, specific items, specific categories, etc.

## Folders
#### static
This folder contains the `style.css` file that defines the base styles for the web application.

#### templates
This folder contains all the HTML templates for the web application.