import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]
  return current_questions

  # create and configure the app
def create_app(test_config=None):
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={'/':{'origins': '*'}})

  # CORS HEADERS
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
      return response 

  @app.route('/categories')
  def retrieve_categories():
    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
      categories_dict[category.id]=category.type

    if (len(categories_dict)==0):
      abort(404)

    return jsonify({
      'success': True,
      'categories': categories_dict
      })

  @app.route('/questions')
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
      categories_dict[category.id] = category.type

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success' : True, 
      'questions' : current_questions, 
      'total_questions': len(Question.query.all()),
      'categories': categories_dict
    })




  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try: 
      question = Question.query.filter(Questions.id == question_id).one_or_none()

      if question is None: 
        abort(404)
      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True, 
        'deleted': question.id, 
        'questions': current_questions, 
        'total_questions': len(Question.query.all())
      })

    except: 
      abort(422)



  @app.route('/questions', methods=['POST'])
  def create_question():
  # this shows the request body 
    body = request.get_json()
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)

    try: 
      question = Question(question = new_question, 
        answer = new_answer, 
        category=new_category, 
        difficulty=new_difficulty)
      question.insert()
      selection=Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)
      return jsonify({
        'success': True, 
        'deleted': question.id, 
        'questions': current_questions, 
        'total_questions': len(Question.query.all())
      })
  except: 
    abort(422)


  @app.route('/questions', methods=['POST'])
  def search_questions():
    try: 
      # search term 
      search_term = request.form.get('search_term', '')
      result = Question.query.filter(Question.question.
          ilike('%{}%'.format(search_term))).all()
      formatted_questions = [question.format() for question in result]

      return jsonify({
        'success': True, 
        'questions': formatted_questions[start:end]
      })
    except: 
      abort(422)




  @app.route('/categories/<int:id>/questions')
  def get_questions_by_category(id):
    category = Category.query.filter_by(id=id).one_or_none()
    if (category is None):
      abort(422)
    selection = Question.query.filter_by(category=category.id).all()
    paginated = paginate_questions(request, selection)

    return jsonify({
      'success': True, 
      'questions': paginated,
      'total_questions': len(Question.query.all()),
      'current_category': category.type
    })


  @app.route('/quizzes', methods=['POST'])
  def play_quiz_question():
   # load the request body
    body = request.get_json()

    # previous question 
    previous = body.get('previous_questions')

    # get category 
    category = body.get('quiz_category')

    # abort 400 if category or previous question isnt found
    if ((category is None) or (previous is None)):
      abort(400)

    # load all questions if all is selected 
    if (category['id']== 0):
      questions = Question.query.all()
    # load questions for a given category 
    else: 
      questions = Question.query.filter_by(category=category['id']).all()

    total = len(questions)

    def random_question():
      return questions[random.randrange(0, len(questions), 1)]
    def check_if_used(question):
      used = False 
      for q in previous: 
        if (q == question.id):
          used = True 
      return used 

    # get random question 
    question = random_question()

    # check if used, execute untl unused question found 
    while (check_if_used(question)):
      question = random_question()

      # if all questions have been tried, return w/o question 
      # necessary if categiry has <5 questions 
      if (len(previous) == total):
        return jsonify({
          'success' : True 
        })

    return jsonify({
      'success' : True, 
      'question' : question.format()
    })





  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False, 
      'error': 404, 
      'message' : 'Resource not found :( '
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success' : False, 
      'error' : 422, 
      'message' : 'unprocessable :('
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success' : False, 
      'error' : 400, 
      'message' : 'bad request :('
    }), 400

  return app
