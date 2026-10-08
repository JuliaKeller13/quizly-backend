<div align="center">

<img
  src="https://raw.githubusercontent.com/Developer-Akademie-Backendkurs/project.Quizly/main/assets/icons/logoheader.png"
  alt="Quizly Logo"
  width="180"
/>

<h1>Quizly Backend</h1>

<p>
  AI-powered quiz generation from YouTube videos,<br>
  built with Django and Django REST Framework.
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-5.2.17-092E20?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/DRF-3.18.1-A30000" alt="Django REST Framework">
  <img src="https://img.shields.io/badge/Coverage-100%25-success" alt="Coverage">
</p>

<p>
  <img src="https://img.shields.io/badge/Whisper-Local-412991" alt="Whisper">
  <img src="https://img.shields.io/badge/Gemini-Flash-4285F4?logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/yt--dlp-YouTube%20Audio-FF0000" alt="yt-dlp">
  <img src="https://img.shields.io/badge/FFmpeg-MP3-007808?logo=ffmpeg&logoColor=white" alt="FFmpeg">
</p>

<p>
  <a href="https://github.com/Developer-Akademie-Backendkurs/project.Quizly">
    <strong>Frontend Repository</strong>
  </a>
  &nbsp;•&nbsp;
  <a href="https://github.com/JuliaKeller13/quizly-backend">
    Backend Repository
  </a>
</p>

</div>

<hr>

<h2>About</h2>

<p>
  <strong>Quizly</strong> turns YouTube videos into automatically generated quizzes.
</p>

<p>
  This repository contains my backend implementation created as part of the
  <strong>Developer Akademie Backend curriculum</strong>.
</p>

<p>
  Authenticated users can submit a YouTube URL. The backend downloads the audio,
  converts it with FFmpeg, transcribes it locally with Whisper and sends the
  transcript to Gemini. The generated quiz is validated and stored together with
  exactly ten questions and four answer options per question.
</p>

<blockquote>
  The frontend was provided by Developer Akademie.
  My main task was to design and implement the Django REST API and the complete
  YouTube-to-quiz processing pipeline.
</blockquote>

<h2>API Overview</h2>

<table>
  <tr>
    <th>Method</th>
    <th>Endpoint</th>
    <th>Resource</th>
  </tr>
  <tr>
    <td>POST</td>
    <td><code>/api/register/</code></td>
    <td>Registration</td>
  </tr>
  <tr>
    <td>POST</td>
    <td><code>/api/login/</code></td>
    <td>Login</td>
  </tr>
  <tr>
    <td>POST</td>
    <td><code>/api/token/refresh/</code></td>
    <td>Refresh access token</td>
  </tr>
  <tr>
    <td>POST</td>
    <td><code>/api/logout/</code></td>
    <td>Logout</td>
  </tr>
  <tr>
    <td>GET / POST</td>
    <td><code>/api/quizzes/</code></td>
    <td>Quiz collection</td>
  </tr>
  <tr>
    <td>GET / PATCH / DELETE</td>
    <td><code>/api/quizzes/{quiz_id}/</code></td>
    <td>Quiz detail</td>
  </tr>
</table>

<h2>Authentication</h2>

<p>
  Protected endpoints use JWT authentication with
  <strong>HttpOnly cookies</strong>.
</p>

<p>
  After login, the backend sets:
</p>

<pre><code>access_token
refresh_token</code></pre>

<p>
  Tokens are not stored in <code>localStorage</code> and are not expected in an
  <code>Authorization</code> header.
</p>

<p>
  The access token is read from the cookie for protected requests.
  The refresh token is used by <code>/api/token/refresh/</code> to create a new
  access cookie.
</p>

<p>
  On logout, both cookies are deleted and the current tokens are invalidated.
</p>

<h2>Quiz Generation Pipeline</h2>

<pre>
YouTube URL
    │
    ▼
  yt-dlp
    │
    ▼
  FFmpeg
    │
    ▼
 MP3 Audio
    │
    ▼
  Whisper
    │
    ▼
 Transcript
    │
    ▼
 Gemini Flash
    │
    ▼
 JSON Response
    │
    ▼
 Validation
    │
    ▼
Quiz + 10 Questions
    │
    ▼
 Database
</pre>

<p>
  Supported YouTube URLs are normalized before they are stored.
</p>

<p>Example:</p>

<pre><code>https://youtu.be/abc123XYZ89</code></pre>

<p>is stored as:</p>

<pre><code>https://www.youtube.com/watch?v=abc123XYZ89</code></pre>

<p>
  Gemini responses are parsed from plain text. Markdown JSON fences are removed
  before the response is processed with <code>json.loads()</code>.
</p>

<h2>Setup</h2>

<h3>1. Clone the repository</h3>

<pre><code>git clone https://github.com/JuliaKeller13/quizly-backend.git
cd quizly-backend</code></pre>

<h3>2. Create and activate a virtual environment</h3>

<h4>Windows PowerShell</h4>

<pre><code>python -m venv .venv
.\.venv\Scripts\Activate.ps1</code></pre>

<h4>macOS / Linux</h4>

<pre><code>python3 -m venv .venv
source .venv/bin/activate</code></pre>

<h3>3. Install Python dependencies</h3>

<pre><code>python -m pip install -r requirements.txt</code></pre>

<h3>4. Install FFmpeg</h3>

<p>
  FFmpeg must be installed globally and available through the system
  <code>PATH</code>.
</p>

<p>Check the installation:</p>

<pre><code>ffmpeg -version
ffprobe -version</code></pre>

<h3>5. Configure the environment</h3>

<p>
  Create a local <code>.env</code> file in the project root.
  Use <code>.env.template</code> as a reference:
</p>

<pre><code>SECRET_KEY=your-secret-key-here
FRONTEND_URLS=http://127.0.0.1:5500,http://localhost:5500
GEMINI_API_KEY=your-gemini-api-key-here</code></pre>

<blockquote>
  <strong>Important:</strong>
  Never commit the real <code>.env</code> file, secret key or Gemini API key.
</blockquote>

<h3>6. Prepare the database</h3>

<pre><code>python manage.py migrate</code></pre>

<h3>7. Create a superuser</h3>

<p>
  Create an administrator account for access to the Django Admin interface:
</p>

<pre><code>python manage.py createsuperuser</code></pre>

<h3>8. Start the server</h3>

<pre><code>python manage.py runserver</code></pre>

<p>Backend:</p>

<pre><code>http://127.0.0.1:8000/</code></pre>

<p>Django Admin:</p>

<pre><code>http://127.0.0.1:8000/admin/</code></pre>

<h2>Frontend</h2>

<p>
  The frontend was provided by Developer Akademie:
</p>

<p>
  <a href="https://github.com/Developer-Akademie-Backendkurs/project.Quizly">
    github.com/Developer-Akademie-Backendkurs/project.Quizly
  </a>
</p>

<p>
  For local development it connects to:
</p>

<pre><code>http://127.0.0.1:8000/api/</code></pre>

<p>
  Requests to protected endpoints must include credentials so that the browser
  sends the authentication cookies.
</p>

<h2>Testing</h2>

<p>Run all tests:</p>

<pre><code>python manage.py test --settings=core.settings_test</code></pre>

<p>Run coverage:</p>

<pre><code>python -m coverage erase
python -m coverage run manage.py test --settings=core.settings_test
python -m coverage report -m</code></pre>

<p>Run Django's system check:</p>

<pre><code>python manage.py check</code></pre>

<div align="center">

<img
  src="https://img.shields.io/badge/Application%20Coverage-100%25-success"
  alt="100 percent application coverage"
/>

</div>

<h2>Project Structure</h2>

<pre>
quizly-backend/
├── core/
│   ├── settings.py
│   ├── settings_test.py
│   └── urls.py
├── quizzes/
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── tests/
│   ├── admin.py
│   ├── models.py
│   ├── prompts.py
│   └── utils.py
├── users/
│   ├── api/
│   │   ├── authentication.py
│   │   ├── exceptions.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── tests/
│   ├── models.py
│   └── utils.py
├── .coveragerc
├── .env.template
├── manage.py
└── requirements.txt
</pre>

<h2>Key Implementation Details</h2>

<p>
  <strong>YouTube processing:</strong>
  <code>yt-dlp</code> downloads the best available audio stream and FFmpeg
  extracts an MP3 file for transcription.
</p>

<p>
  <strong>Whisper:</strong>
  transcription runs locally. Audio is not sent to an external transcription
  service.
</p>

<p>
  <strong>Gemini:</strong>
  the transcript is sent to Gemini Flash with a strict prompt requiring valid
  JSON, exactly ten questions and four distinct answer options per question.
</p>

<p>
  <strong>Validation:</strong>
  generated quiz data is validated before it is stored. The correct answer must
  exist in the corresponding answer options.
</p>

<p>
  <strong>Temporary files:</strong>
  downloaded audio is removed after processing, including when the generation
  pipeline raises an error.
</p>

<h2>Project Context</h2>

<p>
  Quizly was implemented as a learning project within the
  <strong>Developer Akademie Backend curriculum</strong>.
</p>

<p>
  The frontend was provided as the client application.
  My main task was to implement the backend architecture, authentication,
  REST API, AI integration, media processing and automated test suite.
</p>

<p>
  The finished backend has been verified with automated tests,
  <strong>100% application coverage</strong>, Django system checks and a real
  end-to-end YouTube-to-quiz request returning HTTP <code>201</code>.
</p>

<hr>

<div align="center">

<img
  src="https://raw.githubusercontent.com/Developer-Akademie-Backendkurs/project.Quizly/main/assets/icons/logoheader.png"
  alt="Quizly Logo"
  width="90"
/>

<h3>Julia Keller</h3>

<p>
  <a href="https://github.com/JuliaKeller13">GitHub</a>
  &nbsp;•&nbsp;
  <a href="https://github.com/JuliaKeller13/quizly-backend">Backend</a>
  &nbsp;•&nbsp;
  <a href="https://github.com/Developer-Akademie-Backendkurs/project.Quizly">Frontend</a>
</p>

<p>
  Developed as part of the Developer Akademie GmbH advanced training program.
</p>

</div>
