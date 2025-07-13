# AI Student - Premium Web Application

A modern, mobile-friendly Django web application for transforming YouTube videos into smart study notes with AI-powered summaries, intelligent timestamps, and downloadable PDFs.

## 🎯 Features

- **Premium Dark UI**: Elegant blackish-blue gradient design with soft-glow highlights
- **Mobile-First Design**: Fully responsive across all devices
- **AI-Powered Summarization**: Uses Google Gemini and Mistral-7B for intelligent content analysis
- **Smart Timestamps**: Automatically generated section breaks with descriptive titles
- **PDF Generation**: Beautifully formatted downloadable summaries
- **Real-time Processing**: Live loading animations and progress indicators
- **Error Handling**: Comprehensive error management with helpful suggestions

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- API keys for Google Gemini and Together.ai

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd "Youtube Summarizer/yt_study_bot"
   ```

2. **Activate virtual environment:**
   ```bash
   # Windows
   env\Scripts\activate
   
   # macOS/Linux
   source env/bin/activate
   ```

3. **Install web dependencies:**
   ```bash
   pip install -r requirements_web.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   TOGETHER_API_KEY=your_together_api_key_here
   ```

5. **Run the application:**
   ```bash
   python run_web.py
   ```

6. **Access the application:**
   Open your browser and go to: `http://localhost:8000`

## 📁 Project Structure

```
yt_study_bot/
├── ai_student_web/          # Django project settings
│   ├── settings.py         # Main Django configuration
│   ├── urls.py            # Project URL routing
│   └── wsgi.py            # WSGI configuration
├── summarizer/             # Main Django app
│   ├── views.py           # View logic and API endpoints
│   ├── urls.py            # App URL routing
│   └── apps.py            # App configuration
├── templates/              # HTML templates
│   ├── base.html          # Base template with dark UI
│   └── summarizer/        # App-specific templates
│       ├── home.html      # Home page with input form
│       └── result.html    # Results display page
├── static/                 # Static files
│   ├── css/
│   │   └── styles.css     # Premium dark UI styles
│   └── js/
│       └── main.js        # Interactive JavaScript
├── core_summarizer.py     # Core video processing logic
├── llm_handler.py         # Multi-LLM provider handler
├── pdf_generator.py       # PDF generation module
├── manage.py              # Django management script
├── run_web.py            # Quick start script
└── requirements_web.txt   # Web app dependencies
```

## 🎨 UI/UX Features

### Premium Dark Theme
- **Background**: Blackish-blue gradient (`#0a0a0f` to `#16213e`)
- **Text**: Sharp white text with proper contrast
- **Accents**: Soft-glow highlights in teal (`#00d4aa`)
- **Cards**: Elegant glass-morphism effect with subtle borders

### Mobile-First Design
- **Responsive Grid**: Adapts to all screen sizes
- **Touch-Friendly**: Large buttons and touch targets
- **Optimized Typography**: Readable on mobile devices
- **Smooth Animations**: 60fps transitions and hover effects

### Interactive Elements
- **Loading Animations**: Step-by-step progress indicators
- **Hover Effects**: Subtle lift animations on cards
- **Error Handling**: Modal dialogs with helpful suggestions
- **Success Notifications**: Toast messages for user feedback

## 🔧 Technical Stack

### Backend
- **Django 5.0**: Modern Python web framework
- **Python 3.8+**: Latest Python features
- **SQLite**: Lightweight database (can be upgraded to PostgreSQL)

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid and Flexbox
- **Vanilla JavaScript**: No frameworks, optimized performance
- **Font Awesome**: Professional icons

### AI Integration
- **Google Gemini**: Primary AI provider for summarization
- **Mistral-7B**: Fallback AI provider via Together.ai
- **Multi-LLM Handler**: Automatic failover and load balancing

## 📱 Mobile Responsiveness

The application is fully optimized for mobile devices:

- **Breakpoints**: 480px, 768px, 1024px
- **Touch Targets**: Minimum 44px for all interactive elements
- **Typography**: Scalable font sizes using CSS custom properties
- **Navigation**: Simplified mobile navigation
- **Forms**: Mobile-optimized input fields and buttons

## 🎯 Key Features

### 1. Video Processing
- **URL Validation**: Real-time YouTube URL validation
- **Subtitle Extraction**: Fast subtitle-based processing
- **Error Handling**: Comprehensive error messages and suggestions

### 2. AI Summarization
- **Executive Summary**: Quick overview of main points
- **Smart Timestamps**: Intelligent section breaks
- **Full Summary**: Comprehensive content breakdown
- **Multi-LLM**: Automatic failover between AI providers

### 3. PDF Generation
- **Professional Layout**: Clean, academic-style formatting
- **Downloadable**: One-click PDF download
- **Offline Access**: Complete summaries for offline study

### 4. User Experience
- **Loading States**: Real-time progress indicators
- **Error Recovery**: Helpful error messages and suggestions
- **Success Feedback**: Confirmation messages for actions
- **Smooth Navigation**: Seamless page transitions

## 🔒 Security Features

- **CSRF Protection**: Built-in Django CSRF protection
- **Input Validation**: Server-side URL validation
- **Session Management**: Secure session handling
- **XSS Prevention**: Content Security Policy headers
- **HTTPS Ready**: Production-ready security settings

## 🚀 Deployment

### Development
```bash
python run_web.py
```

### Production
1. Set `DEBUG = False` in settings.py
2. Configure production database (PostgreSQL recommended)
3. Set up static file serving (nginx/Apache)
4. Use production WSGI server (Gunicorn/uWSGI)
5. Configure HTTPS with SSL certificates

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements_web.txt
   ```

2. **API Key Errors**: Verify your `.env` file contains valid API keys
   ```env
   GOOGLE_API_KEY=your_actual_key_here
   TOGETHER_API_KEY=your_actual_key_here
   ```

3. **Static Files Not Loading**: Run collectstatic
   ```bash
   python manage.py collectstatic
   ```

4. **Database Errors**: Run migrations
   ```bash
   python manage.py migrate
   ```

### Getting Help

- Check the console for error messages
- Verify API keys are valid and have sufficient quota
- Ensure all dependencies are properly installed
- Check network connectivity for API calls

## 📈 Performance

- **Processing Speed**: 10-20x faster than audio-based systems
- **Page Load**: Optimized static assets and minimal JavaScript
- **Mobile Performance**: Optimized for mobile network conditions
- **Caching**: Static file caching and session management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini**: For powerful AI summarization
- **Together.ai**: For reliable Mistral-7B access
- **Django**: For the robust web framework
- **Font Awesome**: For beautiful icons

---

**Made for students by students** 🎓

*Developed with ❤️ for the educational community* 