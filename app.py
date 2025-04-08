from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
import sqlite3
import requests
import openai
import os
import time

# Initialize Flask app
app = Flask(__name__)

# API Keys
SPOONACULAR_API_KEY = "Add your API KEY"

# Temporary storage for saved recipes (in-memory for simplicity)
saved_recipes = []

# Create temp directory for TTS files
if not os.path.exists("temp"):
    os.makedirs("temp")

# Home Route
@app.route('/')
def home():
    connection = sqlite3.connect('recipe_assistant.db')
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM recipes")
    recipe_names = cursor.fetchall()
    connection.close()

    try:
        spoonacular_url = "https://api.spoonacular.com/recipes/random"
        params = {"number": 3, "apiKey": SPOONACULAR_API_KEY}
        response = requests.get(spoonacular_url, params=params)

        if response.status_code == 200:
            spoonacular_recipes = response.json().get("recipes", [])
        else:
            spoonacular_recipes = []
    except Exception:
        spoonacular_recipes = []

    return render_template(
        'index.html',
        recipe_names=recipe_names,
        spoonacular_recipes=spoonacular_recipes
    )

# Fetch Recipe Route
@app.route('/fetch_recipe', methods=['POST'])
def fetch_recipe():
    recipe_name = request.form['recipe_name'].strip()
    category = request.form['category']

    connection = sqlite3.connect('recipe_assistant.db')
    cursor = connection.cursor()

    if category:
        cursor.execute("SELECT * FROM recipes WHERE LOWER(name) = LOWER(?) AND category = ?", (recipe_name, category))
    else:
        cursor.execute("SELECT * FROM recipes WHERE LOWER(name) = LOWER(?)", (recipe_name,))

    recipe = cursor.fetchone()
    connection.close()

    if recipe:
        return render_template('recipe_details.html', recipe=recipe)
    else:
        return "Recipe not found!"

# Save Recipe Route
@app.route('/save_recipe', methods=['POST'])
def save_recipe():
    recipe_name = request.form.get('recipe_name')
    ingredients = request.form.get('ingredients')
    instructions = request.form.get('instructions')
    category = request.form.get('category')
    health_tag = request.form.get('health_tag')

    saved_recipes.append({
        'name': recipe_name,
        'ingredients': ingredients,
        'instructions': instructions,
        'category': category,
        'health_tag': health_tag
    })

    return redirect(url_for('view_saved_recipes'))

# View Saved Recipes Route
@app.route('/view_saved_recipes', methods=['GET'])
def view_saved_recipes():
    return render_template('view_saved_recipes.html', recipes=saved_recipes)

# AI-Generated Recipe Function
def generate_recipe(prompt):
    openai.api_key = OPENAI_API_KEY
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Generate a recipe using the following ingredients: {prompt}",
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/generate-recipe', methods=['POST'])
def generate_recipe_route():
    try:
        data = request.json
        prompt = data.get('ingredients', '').strip()
        if not prompt:
            return jsonify({'error': 'No ingredients provided'}), 400
        recipe = generate_recipe(prompt)
        return jsonify({'recipe': recipe})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
