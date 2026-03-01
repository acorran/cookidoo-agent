---
applyTo: '**'
---
# Project Context and Coding Guidelines
## Project Requirements

- Create an LLM assistant that interacts with the Cookidoo platform.
- Leverage open source API clients to interact with the Cookidoo platform.
- The agent should:
  - Take a prompt of an existing recipe.
  - Accept user modifications.
  - Generate a new recipe based on the modifications.
  - Save the new recipe to "My Cookidoo Recipes".
- Enable tweaking of existing recipes and saving them as personal recipes, since Cookidoo lacks an export feature.
- Answer questions about recipes, ingredients, and cooking techniques available on the Cookidoo platform.
- Output a shopping list based on selected recipes.
- Provide or integrate an MCP server to interact with the Cookidoo API and platform.
- Ensure credentials for Cookidoo access are securely managed and not exposed in the codebase (e.g., use Azure Key Vault).
- Implement logging and error handling to track the agent's activities and handle issues during operation.
- Use Databricks to store recipe data in a DLT and user interactions for analysis and improvement of the agent's performance over time.
- Provide Databricks notebooks to explore and visualize the data stored in the DLT.
- Use AgentBricks to manage the LLM agent's workflows and interactions with the Cookidoo platform.
- Train the agent model using relevant datasets to improve its understanding of cooking-related queries and recipe generation.
- Provide steps on how to deploy the agent in a production environment.
- If an MCP is available in the Databricks environment, provide steps to set it up and integrate with the Cookidoo API.
- Deliver a fully functional LLM agent that can:
  - Assist with recipe generation.
  - Answer cooking-related questions.
  - Manage shopping lists.
  - Ensure security, logging, and data analysis capabilities.
  - Integrate with Databricks and AgentBricks ecosystems to showcase Databricks AI features and LLMs in enhancing cooking experiences through automation and intelligent assistance.
- Make the LLM accessible via an API endpoint for easy integration.
- Create a website so users can interact with the agent seamlessly, ideally using a front-end framework like React and a backend with FastAPI or Flask.
- Deploy the entire solution using Docker containers for scalability and ease of deployment to Azure Container Apps.
- Provide comprehensive documentation covering setup, deployment, and usage instructions for future reference.
- Create a PRD (Product Requirements Document) outlining the features, functionalities, and technical specifications of the LLM agent for Cookidoo platform integration.
## Coding Guidelines
- Follow PEP 8 coding standards for Python code.

- Use meaningful variable and function names that clearly describe their purpose.

- Write modular code by breaking down functionalities into smaller, reusable functions or classes.
- Include docstrings for all functions and classes to explain their purpose, parameters, and return values.
- Implement error handling using try-except blocks to manage exceptions gracefully.
- Use logging to track the application's flow and record important events or errors.
- Write unit tests for critical functions to ensure code reliability and facilitate future maintenance.
- Use version control (e.g., Git) to manage code changes and collaborate with others effectively
- Ensure sensitive information (e.g., API keys, credentials) is securely managed and not hard-coded in the codebase.
- Optimize code for performance and efficiency where applicable.  
- Regularly review and refactor code to improve readability and maintainability.  
- Document the setup and deployment process clearly for future reference.
- Use virtual environments to manage project dependencies and avoid conflicts.
- Adhere to security best practices, especially when handling user data and external API interactions.  
- Ensure compatibility with the target deployment environment (e.g., Azure Container Apps).
- Follow best practices for API design if creating custom endpoints for the LLM agent.
- Use consistent formatting and indentation throughout the codebase.
- Leverage existing libraries and frameworks where appropriate to avoid reinventing the wheel.
- Stay updated with the latest developments in LLMs, Databricks, and AgentBricks to incorporate new features and improvements into the project.
- Ensure the code is scalable to handle increased load or additional features in the future.
- Conduct code reviews with peers to maintain code quality and share knowledge. 
- Maintain a clear separation of concerns between different components (e.g., front-end, back-end, data storage).
