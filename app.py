from flask import Flask
from flask import render_template, request, url_for, redirect
from markupsafe import escape
from newspaper import Article
import openai
import os

# Set up the OpenAI API client
# openai.api_key = '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'
openai.api_key = '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'

# Set up the model and prompt
model_engine = "text-davinci-003"

app = Flask(__name__)


@app.route('/', methods =["GET", "POST"])
def index():
    os.system('rm -rf responses.txt')
    return render_template('./start.html')


@app.route('/end/<score>', methods =["GET", "POST"])
def end(score):
    with open('questions.txt','r') as f:
        questions = eval(f.read())
    return render_template('./end.html', score=score, total=len(questions))


@app.route('/answers', methods =["GET", "POST"])
def show_answers():
    nquestions = []
    noptions = []
    nanswers = []

    with open('questions.txt','r') as f:
        questions = eval(f.read())

    with open('options.txt','r') as f:
        options = eval(f.read())

    with open('answers.txt','r') as f:
        answers = eval(f.read())

    with open('content.txt', 'r') as f:
        content = f.read()

    prompt = content + f" Generate the summary of the above text"

    print(prompt)

    # Generate a response
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=1,
    )

    res = completion.choices[0].text

    # print(res)

    for i in range(len(questions)):
        nquestions.append('<h2> ' + questions[i] + ' </h2>')

    for i in range(len(options)):
        lst = []
        for j in range(4):
            lst.append('<p> ' + options[i][j] + ' </p>')
        
        noptions.append(lst)
        # options[i][4] += ' <br> '

    for i in range(len(answers)):
        nanswers.append('<h3> Answer: '+answers[i]+' </h3> <br>')
    
    text = '<br><h1> Summary </h1><hr>'
    text += '<h4>'+res+'</h4><hr>'
    text += '<br><h1> Answers </h1><hr> '
    for i in range(len(questions)):
        text += nquestions[i]
        for j in range(4):
            text += noptions[i][j]
        text += nanswers[i]

    return text


@app.route('/quiz', methods =["GET", "POST"])
def prepare_quiz():
    if request.method == "POST":
        link = request.form.get('link')
        article = Article(link)
        article.download()
        article.parse()
    
        content = article.title + '\n' + article.text

        with open('content.txt', 'w') as f:
            f.write(content)

        prompt = content + f" Generate 5 MCQs with 4 options each. Also put answers at the end of each question"

        # Generate a response
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=1,
        )

        res = completion.choices[0].text

        lines = res.split('\n')
        goodlines = []
        for line in lines:
            if line == '' or line=='\n':
                continue
            goodlines.append(line)

        questions = []
        options = []
        answers = []

        for i in range(len(goodlines)):
            line = goodlines[i]
            if line.endswith('?'):
                questions.append(line)
                options.append([goodlines[i+1],goodlines[i+2],goodlines[i+3],goodlines[i+4]])
                answers.append(goodlines[i+5].split()[1][0])

        # print(goodlines)
        # print(questions)
        # print(answers)

        with open('questions.txt','w') as f:
            f.write(str(questions))

        with open('options.txt','w') as f:
            f.write(str(options))

        with open('answers.txt','w') as f:
            f.write(str(answers))

    
    # return render_template('./quiz.html', idx=1, question=questions[0], options=options[0])
    return redirect(url_for('quiz', idx=1))


responses = []

@app.route('/quiz/<int:idx>', methods =["GET", "POST"])
def quiz(idx):
    with open('questions.txt','r') as f:
        questions = eval(f.read())

    with open('options.txt','r') as f:
        options = eval(f.read())

    with open('answers.txt','r') as f:
        answers = eval(f.read())


    if request.method == "POST":
        ans1 = request.form.get('option1')
        ans2 = request.form.get('option2')
        ans3 = request.form.get('option3')
        ans4 = request.form.get('option4')

        ans = 'X'

        if ans4 is not None:
            ans = ans4

        if ans3 is not None:
            ans = ans3

        if ans2 is not None:
            ans = ans2

        if ans1 is not None:
            ans = ans1

        if idx == 1:
            with open('responses.txt','w') as f:
                f.write(ans)
        else:
            with open('responses.txt','a') as f:
                f.write(ans)

        with open('responses.txt','r') as f:
            responses = f.read()

        print(responses)

        if idx == len(questions)+1:
            score = 0
            for i in range(len(questions)):
                if responses[i].lower()==answers[i][-1].lower():
                    print(responses[i],answers[i][-1])
                    score += 1
            
            return redirect(f'/end/{score}')

        # print(questions)
        # print(options)

        return render_template('./quiz.html', idx=idx, question=questions[idx-1], options=options[idx-1])

    return render_template('./quiz.html', idx=idx, question=questions[idx-1], options=options[idx-1])


if __name__ == '__main__':
    app.run('127.0.0.1',port=3001)