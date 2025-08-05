class PromptBuilder:
    """Builds a text-to-SQL prompt for an LLM."""

    @staticmethod
    def build(schema, question, db_type='sqlite'):
        """
        Constructs the full prompt string.

        Args:
            schema (dict): The database schema from SchemaExtractor.
            question (str): The user's natural language question.
            db_type (str): The SQL dialect to use (e.g., 'sqlite', 'mysql').

        Returns:
            str: A formatted prompt ready for the LLM.
        """
        
        dialect_settings = {
            'sqlite': {
                'limit_syntax': 'LIMIT',
                'quote_char': '"',
                'functions': ['SUBSTR', 'LENGTH', 'UPPER', 'LOWER', 'DATE', 'DATETIME']
            },
            'postgresql': {
                'limit_syntax': 'LIMIT',
                'quote_char': '"',
                'functions': ['SUBSTRING', 'LENGTH', 'UPPER', 'LOWER', 'EXTRACT', 'NOW()']
            },
            'mssql': {
                'limit_syntax': 'TOP',
                'quote_char': '[',
                'functions': ['SUBSTRING', 'LEN', 'UPPER', 'LOWER', 'GETDATE()', 'DATEPART']
            }
        }
        
        current_dialect = dialect_settings.get(db_type.lower(), dialect_settings['sqlite'])
        
        prompt = f"### Instructions:\n"
        prompt += f"Your task is to convert a user's question into a syntactically correct {db_type.upper()} SQL query. "
        prompt += "You must only respond with the SQL query, without any additional text, explanations, or markdown formatting.\n"
        prompt += "Use the provided database schema to ensure the query is valid.\n\n"
        
        prompt += f"### {db_type.upper()} Syntax Guidelines:\n"
        if db_type.lower() == 'mssql':
            prompt += "- Use TOP N instead of LIMIT N for row limiting\n"
            prompt += "- Use [column_name] for quoting identifiers\n"
            prompt += "- Use GETDATE() for current timestamp\n"
        elif db_type.lower() == 'postgresql':
            prompt += "- Use LIMIT N for row limiting\n"
            prompt += '- Use "column_name" for quoting identifiers\n'
            prompt += "- Use NOW() for current timestamp\n"
        else:  # sqlite
            prompt += "- Use LIMIT N for row limiting\n"
            prompt += '- Use "column_name" for quoting identifiers\n'
            prompt += "- Use DATETIME('now') for current timestamp\n"
        prompt += "\n"

        prompt += "### Database Schema:\n"
        prompt += "The database has the following tables and columns:\n"
        for table_name, details in schema.items():
            columns_str = ", ".join(details['columns'])
            prompt += f"Table `{table_name}` has columns: `{columns_str}`\n"
        prompt += "\n"

        prompt += "### User Question:\n"
        prompt += f'"{question}"\n\n'

        prompt += "### SQL Query:\n"
        
        return prompt

