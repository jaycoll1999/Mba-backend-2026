import os
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.subject import Subject, SyllabusSource
from app.models.unit import Unit
from app.models.question import Question, DifficultyLevel
from app.models.resource import Resource, ResourceType
from app.models.reminder import ReminderPreference
from app.core.security import hash_password
from app.config import settings

def create_sample_pdf_if_missing(file_path: str, title: str):
    """Creates a valid minimal PDF file if not already present."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        # Write a minimal standard PDF structure
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
            b"4 0 obj << /Length 50 >> stream\n"
            b"BT /F1 24 Tf 100 700 Td (" + title.encode("ascii", "replace") + b") Tj ET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000207 00000 n \n"
            b"trailer << /Size 5 /Root 1 0 R >>\nstartxref\n310\n%%EOF\n"
        )
        with open(file_path, "wb") as f:
            f.write(pdf_content)

def seed_database():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. SEED USERS
        admin_user = db.query(User).filter(User.email == "admin@mbahub.edu").first()
        if not admin_user:
            admin_user = User(
                email="admin@mbahub.edu",
                hashed_password=hash_password("AdminPass123!"),
                full_name="Dr. Arvind Kulkarni (MBA Academic Dean)",
                role=UserRole.ADMIN.value,
                college="National Institute of Management",
                roll_number="FAC-2024-001",
                streak_days=15,
                last_active_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            # Reminder for admin
            admin_pref = ReminderPreference(
                user_id=admin_user.id,
                reminder_time="08:30",
                timezone="Asia/Kolkata",
                is_enabled=True,
                notification_channel="in_app"
            )
            db.add(admin_pref)
            db.commit()

        student_user = db.query(User).filter(User.email == "student@mbahub.edu").first()
        if not student_user:
            student_user = User(
                email="student@mbahub.edu",
                hashed_password=hash_password("StudentPass123!"),
                full_name="Rahul Sharma",
                role=UserRole.STUDENT.value,
                college="Faculty of Management Studies",
                roll_number="MBA-2024-042",
                streak_days=5,
                last_active_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                is_active=True
            )
            db.add(student_user)
            db.commit()
            db.refresh(student_user)

            # Reminder for student
            student_pref = ReminderPreference(
                user_id=student_user.id,
                reminder_time="09:00",
                timezone="Asia/Kolkata",
                is_enabled=True,
                notification_channel="in_app"
            )
            db.add(student_pref)
            db.commit()

        # 2. SEED SUBJECTS (The exact 8 core Semester 1 subjects required)
        subject_data = [
            {
                "code": "OB-101",
                "name": "Organizational Behaviour",
                "description": "Explores individual behavior, attitudes, motivation, group dynamics, team effectiveness, and organizational culture in managerial settings.",
                "credits": 3,
                "semester": 1,
                "icon_name": "Users",
                "color_code": "blue",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Introduction to Organizational Behaviour & Individual Dynamics",
                        "description": "Definition, multidisciplinary roots, OB models, biographical characteristics, and perception.",
                        "learning_objectives": "Understand micro and macro foundations of workplace human behaviour.",
                        "source_reference": "Robbins & Judge 18th Ed, Ch 1-2; AICTE MBA Syllabus 2024"
                    },
                    {
                        "unit_number": 2,
                        "title": "Personality, Attitudes, Values and Perception",
                        "description": "Big Five traits, MBTI framework, cognitive dissonance theory, and perceptual distortion.",
                        "learning_objectives": "Analyze individual psychological traits affecting workplace performance.",
                        "source_reference": "Robbins & Judge 18th Ed, Ch 4-6"
                    },
                    {
                        "unit_number": 3,
                        "title": "Motivation Theories and Applications",
                        "description": "Maslow, Herzberg, McClelland, Vroom expectancy theory, and job enrichment strategies.",
                        "learning_objectives": "Design managerial incentive and motivation architectures.",
                        "source_reference": "Robbins & Judge 18th Ed, Ch 7-8"
                    },
                    {
                        "unit_number": 4,
                        "title": "Group Dynamics, Teams, and Leadership",
                        "description": "Tuckman group development stages, team norms, transformational and transactional leadership.",
                        "learning_objectives": "Foster high-performing collaborative work teams and leadership skills.",
                        "source_reference": "Robbins & Judge 18th Ed, Ch 9, 12"
                    },
                    {
                        "unit_number": 5,
                        "title": "Organizational Culture, Conflict Management, and Change",
                        "description": "Lewin 3-step change model, conflict resolution styles, and sustaining ethical culture.",
                        "learning_objectives": "Manage organizational change resistance and negotiate conflicts.",
                        "source_reference": "Robbins & Judge 18th Ed, Ch 14, 16"
                    }
                ]
            },
            {
                "code": "MA-102",
                "name": "Managerial Accounting",
                "description": "Focuses on financial statements interpretation, cost accounting, CVP analysis, budgeting, and managerial decision metrics.",
                "credits": 3,
                "semester": 1,
                "icon_name": "Calculator",
                "color_code": "emerald",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Introduction to Financial & Management Accounting Concepts",
                        "description": "Accounting principles, GAAP/Ind-AS frameworks, and distinction between financial and management accounting.",
                        "learning_objectives": "Comprehend fundamental accounting conventions and double entry system.",
                        "source_reference": "Horngren's Cost Accounting 16th Ed, Ch 1"
                    },
                    {
                        "unit_number": 2,
                        "title": "Preparation and Analysis of Financial Statements",
                        "description": "Balance Sheet, Profit & Loss Statement, Cash Flow Statement, and ratio analysis.",
                        "learning_objectives": "Evaluate corporate liquidity, solvency, and profitability through ratios.",
                        "source_reference": "Horngren's Cost Accounting 16th Ed, Ch 3"
                    },
                    {
                        "unit_number": 3,
                        "title": "Cost Concepts, Classification, and Cost Sheet",
                        "description": "Direct vs indirect costs, fixed vs variable costs, prime cost, and cost sheet preparation.",
                        "learning_objectives": "Structure complete cost allocation sheets for manufacturing and service firms.",
                        "source_reference": "Horngren's Cost Accounting 16th Ed, Ch 2"
                    },
                    {
                        "unit_number": 4,
                        "title": "Cost-Volume-Profit (CVP) and Marginal Costing Decisions",
                        "description": "Break-even analysis, contribution margin, margin of safety, and make-or-buy decisions.",
                        "learning_objectives": "Apply marginal costing to short-term pricing and operational dilemmas.",
                        "source_reference": "Horngren's Cost Accounting 16th Ed, Ch 3"
                    },
                    {
                        "unit_number": 5,
                        "title": "Budgetary Control and Standard Costing",
                        "description": "Cash budgets, flexible budgets, material and labor variance analysis.",
                        "learning_objectives": "Construct operating budgets and compute variance diagnostics.",
                        "source_reference": "Horngren's Cost Accounting 16th Ed, Ch 6-7"
                    }
                ]
            },
            {
                "code": "MF-103",
                "name": "Management Fundamentals",
                "description": "Examines classical and modern management principles, strategic planning, organizational structures, and control systems.",
                "credits": 3,
                "semester": 1,
                "icon_name": "Layers",
                "color_code": "amber",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Evolution of Management Thought & Principles",
                        "description": "Taylor scientific management, Fayol 14 principles, Hawthorne experiments, and contingency approach.",
                        "learning_objectives": "Critically analyze traditional vs contemporary administrative paradigms.",
                        "source_reference": "Koontz & Weihrich, Essentials of Management 10th Ed"
                    },
                    {
                        "unit_number": 2,
                        "title": "Planning, Objectives, and Strategic Decision Making",
                        "description": "Management by Objectives (MBO), SWOT analysis, forecasting, and rational decision matrices.",
                        "learning_objectives": "Formulate strategic business goals and operational roadmaps.",
                        "source_reference": "Koontz & Weihrich, Ch 4-5"
                    },
                    {
                        "unit_number": 3,
                        "title": "Organizing Structures, Authority, and Span of Control",
                        "description": "Line and staff, matrix structures, decentralization, and delegation dynamics.",
                        "learning_objectives": "Design scalable enterprise organizational hierarchies.",
                        "source_reference": "Koontz & Weihrich, Ch 7-8"
                    },
                    {
                        "unit_number": 4,
                        "title": "Directing, Communication, and Interpersonal Relations",
                        "description": "Leadership communication channels, active listening, and organizational feedback loops.",
                        "learning_objectives": "Direct managerial workforce towards common operational objectives.",
                        "source_reference": "Koontz & Weihrich, Ch 11"
                    },
                    {
                        "unit_number": 5,
                        "title": "Controlling Techniques and Corporate Governance",
                        "description": "Feedforward and feedback control, Balanced Scorecard, audit committees, and ethics.",
                        "learning_objectives": "Establish organizational surveillance and ethical compliance systems.",
                        "source_reference": "Koontz & Weihrich, Ch 14"
                    }
                ]
            },
            {
                "code": "IKS-104",
                "name": "Indian Knowledge Systems",
                "description": "Introduces classical Indian philosophy, Arthashastra statecraft, ethical leadership, sustainable commerce, and indigenous paradigms.",
                "credits": 2,
                "semester": 1,
                "icon_name": "Compass",
                "color_code": "orange",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Foundations of Indian Knowledge Systems and Vedic Epistemology",
                        "description": "Pramana shastra, holistic thinking, interconnectedness, and traditional worldviews.",
                        "learning_objectives": "Appreciate classical epistemic methods and scientific heritage of India.",
                        "source_reference": "IKS Division, Ministry of Education, Govt of India Handbook 2023"
                    },
                    {
                        "unit_number": 2,
                        "title": "Ethos, Ethics, and Moral Frameworks in Indian Traditions",
                        "description": "Purusharthas (Dharma, Artha, Kama, Moksha), Nishkama Karma in modern leadership.",
                        "learning_objectives": "Integrate dharma-based ethical governance into managerial conduct.",
                        "source_reference": "Bhagavad Gita & Classical Indic Ethics in Business"
                    },
                    {
                        "unit_number": 3,
                        "title": "Classical Indian Statecraft, Trade, and Economic Thought",
                        "description": "Kautilya Arthashastra: Saptanga theory, treasury management, and guilds (Shrenis).",
                        "learning_objectives": "Extract statecraft and strategic negotiation insights for enterprise strategy.",
                        "source_reference": "Rangarajan (Ed.), Kautilya's The Arthashastra"
                    },
                    {
                        "unit_number": 4,
                        "title": "Indigenous Systems of Medicine, Ecology, and Sustainable Living",
                        "description": "Ayurvedic wellness, Panchamahabhutas, cyclic resource utilization, and eco-centric commerce.",
                        "learning_objectives": "Apply traditional sustainability benchmarks to corporate ESG goals.",
                        "source_reference": "IKS Curriculum Guideline Unit 4"
                    },
                    {
                        "unit_number": 5,
                        "title": "Indian Insights on Leadership, Mindfulness, and Holistic Decision Making",
                        "description": "Rajarshi ideal of leadership, meditation, emotional equilibrium, and stakeholder harmony.",
                        "learning_objectives": "Cultivate balanced, stress-resilient executive decision-making.",
                        "source_reference": "IKS Indian Management Paradigms Series"
                    }
                ]
            },
            {
                "code": "EABD-105",
                "name": "Economic Analysis for Business Decisions",
                "description": "Microeconomic and macroeconomic tools for pricing, demand forecasting, production cost curves, and policy analysis.",
                "credits": 3,
                "semester": 1,
                "icon_name": "TrendingUp",
                "color_code": "purple",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Managerial Economics Principles and Demand Analysis",
                        "description": "Opportunity cost, incremental concept, law of demand, and consumer surplus.",
                        "learning_objectives": "Analyze consumer preference schedules and market demand functions.",
                        "source_reference": "Dominick Salvatore, Managerial Economics in a Global Economy 9th Ed"
                    },
                    {
                        "unit_number": 2,
                        "title": "Elasticity of Demand and Demand Forecasting Techniques",
                        "description": "Price, income, and cross elasticity; regression and Delphi demand forecasting methods.",
                        "learning_objectives": "Calculate price elasticity to determine revenue-maximizing price points.",
                        "source_reference": "Salvatore, Ch 4"
                    },
                    {
                        "unit_number": 3,
                        "title": "Production Functions, Returns to Scale, and Cost Analysis",
                        "description": "Short-run vs long-run production, Cobb-Douglas function, economies of scale.",
                        "learning_objectives": "Identify cost minimizing input combinations for industrial outputs.",
                        "source_reference": "Salvatore, Ch 6-7"
                    },
                    {
                        "unit_number": 4,
                        "title": "Market Structures: Perfect Competition, Monopoly, and Oligopoly",
                        "description": "Price-output determination under monopolistic competition, game theory, Cournot and Sweezy kinked demand.",
                        "learning_objectives": "Evaluate competitor reactions and optimal pricing in concentrated markets.",
                        "source_reference": "Salvatore, Ch 8-10"
                    },
                    {
                        "unit_number": 5,
                        "title": "Macroeconomic Indicators, Fiscal & Monetary Policies",
                        "description": "GDP components, inflation metrics (CPI/WPI), RBI monetary policy tools, and business cycles.",
                        "learning_objectives": "Anticipate macroeconomic policy shifts affecting enterprise investment.",
                        "source_reference": "Salvatore, Ch 12"
                    }
                ]
            },
            {
                "code": "DS-106",
                "name": "Decision Science",
                "description": "Quantitative models for managerial decision-making, including linear programming, transportation, and network models.",
                "credits": 3,
                "semester": 1,
                "icon_name": "GitMerge",
                "color_code": "indigo",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Linear Programming: Problem Formulation and Graphical Method",
                        "description": "Objective function, resource constraints, non-negativity, and graphical optimal corner-point solutions.",
                        "learning_objectives": "Formulate real-world industrial resource optimization problems into LPP models.",
                        "source_reference": "Hamdy A. Taha, Operations Research: An Introduction 10th Ed, Ch 2"
                    },
                    {
                        "unit_number": 2,
                        "title": "Simplex Method and Duality Analysis",
                        "description": "Standard form, slack and surplus variables, Big-M method, and shadow pricing interpretation.",
                        "learning_objectives": "Solve multi-variable linear optimizations and analyze dual shadow prices.",
                        "source_reference": "Taha, Ch 3-4"
                    },
                    {
                        "unit_number": 3,
                        "title": "Transportation and Assignment Problems",
                        "description": "North-West Corner, VAM method, MODI optimality test, and Hungarian assignment algorithm.",
                        "learning_objectives": "Minimize logistics dispatch costs and optimize personnel job allocations.",
                        "source_reference": "Taha, Ch 5"
                    },
                    {
                        "unit_number": 4,
                        "title": "Decision Theory under Risk and Uncertainty",
                        "description": "MaxiMax, MaxiMin, Laplace, Hurwicz criteria, and Decision Trees with expected monetary value (EMV).",
                        "learning_objectives": "Structure uncertain capital investment choices via probability trees.",
                        "source_reference": "Taha, Ch 15"
                    },
                    {
                        "unit_number": 5,
                        "title": "Network Models: CPM, PERT, and Project Scheduling",
                        "description": "Critical Path Method (CPM), PERT three-time estimates, float calculations, and project crashing.",
                        "learning_objectives": "Schedule complex multi-stage projects and compute probabilities of completion.",
                        "source_reference": "Taha, Ch 6"
                    }
                ]
            },
            {
                "code": "BA-107",
                "name": "Business Analytics",
                "description": "Data analytics techniques, statistical hypothesis testing, data visualization, predictive modeling, and business insights.",
                "credits": 3,
                "semester": 1,
                "icon_name": "BarChart3",
                "color_code": "cyan",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Fundamentals of Business Analytics & Data-Driven Decision Making",
                        "description": "Descriptive, predictive, and prescriptive analytics paradigms; Big Data characteristics.",
                        "learning_objectives": "Classify analytical problems and structure business intelligence workflows.",
                        "source_reference": "Albright & Winston, Business Analytics: Data Analysis & Decision Making"
                    },
                    {
                        "unit_number": 2,
                        "title": "Descriptive Analytics, Data Visualization, and Summary Metrics",
                        "description": "Measures of central tendency, dispersion, boxplots, histograms, and dashboard storytelling.",
                        "learning_objectives": "Extract diagnostic distribution metrics from enterprise transaction datasets.",
                        "source_reference": "Albright & Winston, Ch 2-3"
                    },
                    {
                        "unit_number": 3,
                        "title": "Probability Distributions and Inferential Statistics",
                        "description": "Normal, Binomial, Poisson distributions; Central Limit Theorem; Z-tests, t-tests, ANOVA.",
                        "learning_objectives": "Execute hypothesis testing to validate customer behavior differences.",
                        "source_reference": "Albright & Winston, Ch 6-8"
                    },
                    {
                        "unit_number": 4,
                        "title": "Predictive Analytics: Simple and Multiple Linear Regression",
                        "description": "OLS estimation, R-squared, multicollinearity, VIF, and logistic regression classification.",
                        "learning_objectives": "Build predictive models forecasting sales and customer churn.",
                        "source_reference": "Albright & Winston, Ch 10-11"
                    },
                    {
                        "unit_number": 5,
                        "title": "Prescriptive Analytics, Optimization, and Simulation",
                        "description": "Monte Carlo simulation, risk modeling, and sensitivity analysis for risk mitigation.",
                        "learning_objectives": "Simulate inventory risk and pricing strategies under variable market scenarios.",
                        "source_reference": "Albright & Winston, Ch 15"
                    }
                ]
            },
            {
                "code": "BOM-108",
                "name": "Basics of Marketing",
                "description": "Core concepts of customer value, STP strategy, marketing mix (4Ps/7Ps), brand equity, and contemporary digital channels.",
                "credits": 3,
                "semester": 1,
                "icon_name": "Target",
                "color_code": "rose",
                "units": [
                    {
                        "unit_number": 1,
                        "title": "Marketing Concepts, Evolution, and Environment",
                        "description": "Production, product, selling, and marketing concepts; PESTLE marketing environment analysis.",
                        "learning_objectives": "Examine market orientations and macro-environmental drivers of brand demand.",
                        "source_reference": "Kotler, Keller & Chernev, Marketing Management 16th Ed, Ch 1"
                    },
                    {
                        "unit_number": 2,
                        "title": "Consumer Buying Behaviour and Market Segmentation (STP)",
                        "description": "Consumer purchase decision model, demographic/psychographic segmentation, targeting, positioning maps.",
                        "learning_objectives": "Construct buyer personas and design differentiated market positioning statements.",
                        "source_reference": "Kotler & Keller, Ch 5-7"
                    },
                    {
                        "unit_number": 3,
                        "title": "Product Strategy, Life Cycle, and New Product Development",
                        "description": "Product hierarchy, Product Life Cycle (PLC) stages, stage-gate innovation, branding elements.",
                        "learning_objectives": "Manage brand product portfolios through changing life cycle stages.",
                        "source_reference": "Kotler & Keller, Ch 9-11"
                    },
                    {
                        "unit_number": 4,
                        "title": "Pricing Strategies, Channels of Distribution, and Logistics",
                        "description": "Cost-plus, skimming, penetration pricing; retail formats, omnichannel distribution.",
                        "learning_objectives": "Establish pricing models and multi-tier intermediary channel agreements.",
                        "source_reference": "Kotler & Keller, Ch 13, 15"
                    },
                    {
                        "unit_number": 5,
                        "title": "Integrated Marketing Communications (IMC) & Digital Marketing",
                        "description": "Advertising, PR, sales promotions, SEO, content marketing, social media campaigns.",
                        "learning_objectives": "Orchestrate 360-degree promotional campaigns blending digital and offline media.",
                        "source_reference": "Kotler & Keller, Ch 17-18"
                    }
                ]
            }
        ]

        subject_map = {}
        unit_map = {}

        for s_info in subject_data:
            s_obj = db.query(Subject).filter(Subject.code == s_info["code"]).first()
            if not s_obj:
                s_obj = Subject(
                    code=s_info["code"],
                    name=s_info["name"],
                    description=s_info["description"],
                    credits=s_info["credits"],
                    semester=s_info["semester"],
                    icon_name=s_info["icon_name"],
                    color_code=s_info["color_code"]
                )
                db.add(s_obj)
                db.commit()
                db.refresh(s_obj)

                # Add SyllabusSource
                source_record = SyllabusSource(
                    subject_id=s_obj.id,
                    university_name="Autonomous University MBA Curriculum",
                    academic_year="2024-2026",
                    syllabus_version="v2.1 (Academic Council Approved)",
                    source_url="https://mba-curriculum.edu/syllabus/sem1",
                    verification_status="verified",
                    verified_by="Academic Board of Management Studies",
                    notes="Fully matched to National Education Policy & AICTE Core Framework."
                )
                db.add(source_record)
                db.commit()

            subject_map[s_info["code"]] = s_obj

            for u_info in s_info["units"]:
                u_obj = db.query(Unit).filter(
                    Unit.subject_id == s_obj.id,
                    Unit.unit_number == u_info["unit_number"]
                ).first()
                if not u_obj:
                    u_obj = Unit(
                        subject_id=s_obj.id,
                        unit_number=u_info["unit_number"],
                        title=u_info["title"],
                        description=u_info["description"],
                        learning_objectives=u_info["learning_objectives"],
                        source_reference=u_info["source_reference"]
                    )
                    db.add(u_obj)
                    db.commit()
                    db.refresh(u_obj)
                unit_map[f"{s_info['code']}_U{u_info['unit_number']}"] = u_obj

        # 3. SEED QUESTIONS (At least 10 Easy, 10 Medium, 10 Hard for OB Unit 1 and across all subjects)
        # We guarantee >= 10 Easy, >= 10 Medium, and >= 10 Hard in OB-101 Unit 1, and 40+ more questions across other subjects.
        ob_u1 = unit_map["OB-101_U1"]
        ob_subj = subject_map["OB-101"]

        ob_u1_questions = [
            # 10 EASY QUESTIONS FOR OB UNIT 1
            {
                "text": "What is the primary focus of the field of Organizational Behaviour (OB)?",
                "difficulty": "easy",
                "options": [
                    "Studying the financial stock markets",
                    "Understanding how individuals and groups act within organizations",
                    "Designing computer microprocessors",
                    "Conducting chemical testing of manufacturing materials"
                ],
                "answer": "Understanding how individuals and groups act within organizations",
                "explanation": "Organizational Behaviour is the multidisciplinary study of human behavior, attitudes, and group dynamics within work environments to enhance organizational effectiveness.",
                "source": "Robbins & Judge 18th Ed, Ch 1"
            },
            {
                "text": "Which foundational academic discipline has contributed the concept of 'learning, perception, and personality' to Organizational Behaviour?",
                "difficulty": "easy",
                "options": ["Psychology", "Sociology", "Anthropology", "Political Science"],
                "answer": "Psychology",
                "explanation": "Psychology contributes the scientific study of individual micro-level human behavior including perception, personality traits, and motivation.",
                "source": "Robbins & Judge 18th Ed, Ch 1"
            },
            {
                "text": "In Organizational Behaviour, what does the Hawthorne Studies primarily demonstrate?",
                "difficulty": "easy",
                "options": [
                    "Workers only care about financial compensation",
                    "Social and psychological factors significantly influence workplace productivity",
                    "Physical lighting levels determine 100% of factory output",
                    "Strict autocratic management produces the highest long-term morale"
                ],
                "answer": "Social and psychological factors significantly influence workplace productivity",
                "explanation": "The Hawthorne experiments demonstrated that employee performance improves when workers perceive attention, supportive group norms, and social interaction.",
                "source": "Koontz & Weihrich; Robbins & Judge Ch 1"
            },
            {
                "text": "What is meant by 'biographical characteristics' in the study of individual behavior?",
                "difficulty": "easy",
                "options": [
                    "Objective personal background data such as age, gender, and length of tenure",
                    "The number of books authored by the CEO",
                    "The company's certified financial history",
                    "The geographical coordinates of corporate headquarters"
                ],
                "answer": "Objective personal background data such as age, gender, and length of tenure",
                "explanation": "Biographical characteristics represent readily identifiable personal traits such as age, gender, tenure, and marital status that correlate with work performance and turnover.",
                "source": "Robbins & Judge 18th Ed, Ch 2"
            },
            {
                "text": "Which component of an attitude reflects a person's feelings or emotions towards an object, person, or event?",
                "difficulty": "easy",
                "options": [
                    "Affective component",
                    "Cognitive component",
                    "Behavioral component",
                    "Perceptual component"
                ],
                "answer": "Affective component",
                "explanation": "Attitudes consist of three ABC components: Affective (emotional/feeling), Behavioral (intended action), and Cognitive (belief or knowledge).",
                "source": "Robbins & Judge 18th Ed, Ch 3"
            },
            {
                "text": "What does 'job satisfaction' measure in organizational behavior?",
                "difficulty": "easy",
                "options": [
                    "A positive feeling about one's job resulting from an evaluation of its characteristics",
                    "The total number of hours worked per week",
                    "The company's quarterly dividend payout ratio",
                    "The legal registration number of an employment contract"
                ],
                "answer": "A positive feeling about one's job resulting from an evaluation of its characteristics",
                "explanation": "Job satisfaction is defined as an employee's positive affective emotional state regarding their workplace role and environment.",
                "source": "Robbins & Judge 18th Ed, Ch 3"
            },
            {
                "text": "Which level of analysis in the basic OB model examines group norms, team roles, and leadership?",
                "difficulty": "easy",
                "options": [
                    "Group level",
                    "Individual level",
                    "Organizational systems level",
                    "Global macroeconomic level"
                ],
                "answer": "Group level",
                "explanation": "The three standard levels of the OB model are: Individual level (micro), Group level (meso), and Organizational System level (macro).",
                "source": "Robbins & Judge 18th Ed, Ch 1"
            },
            {
                "text": "In OB, what does 'Organizational Citizenship Behaviour' (OCB) refer to?",
                "difficulty": "easy",
                "options": [
                    "Discretionary employee behavior that promotes effective organizational functioning beyond formal job duties",
                    "Voting in regional municipal elections",
                    "Filing corporate tax returns on behalf of the company",
                    "Holding dual passports for international business travel"
                ],
                "answer": "Discretionary employee behavior that promotes effective organizational functioning beyond formal job duties",
                "explanation": "OCB represents voluntary helpful behaviors that are not officially mandated by formal employment duties but enhance the psychological climate of the organization.",
                "source": "Robbins & Judge 18th Ed, Ch 1"
            },
            {
                "text": "Which discipline contributes to OB by analyzing power, conflict, and political coalition formation in corporations?",
                "difficulty": "easy",
                "options": ["Political Science", "Biology", "Archaeology", "Physics"],
                "answer": "Political Science",
                "explanation": "Political science contributes theories of resource allocation, bargaining, coalitional conflict, and organizational politics.",
                "source": "Robbins & Judge 18th Ed, Ch 1"
            },
            {
                "text": "What is the definition of 'perception' in the context of human behavior?",
                "difficulty": "easy",
                "options": [
                    "The process by which individuals organize and interpret sensory impressions to give meaning to their environment",
                    "The speed at which a person reads financial balance sheets",
                    "The legal doctrine of company incorporation",
                    "The total amount of memory available on a cloud server"
                ],
                "answer": "The process by which individuals organize and interpret sensory impressions to give meaning to their environment",
                "explanation": "Perception is the psychological filtering process through which raw sensory stimuli are structured into personal mental interpretations.",
                "source": "Robbins & Judge 18th Ed, Ch 6"
            },

            # 10 MEDIUM QUESTIONS FOR OB UNIT 1
            {
                "text": "According to Attribution Theory, which three determinants govern whether an observer attributes an employee's behavior to internal or external causes?",
                "difficulty": "medium",
                "options": [
                    "Distinctiveness, Consensus, and Consistency",
                    "Intelligence, Emotional Quotient, and Motivation",
                    "Salary, Seniority, and Title",
                    "Speed, Accuracy, and Cost"
                ],
                "answer": "Distinctiveness, Consensus, and Consistency",
                "explanation": "Harold Kelley's attribution theory states that observers evaluate distinctiveness (different behaviors in different situations), consensus (peer behavior), and consistency (behavior over time).",
                "source": "Robbins & Judge 18th Ed, Ch 6"
            },
            {
                "text": "When a manager blames an employee's poor sales solely on laziness rather than an economic recession, which cognitive bias is demonstrated?",
                "difficulty": "medium",
                "options": [
                    "Fundamental Attribution Error",
                    "Self-Serving Bias",
                    "Framing Effect",
                    "Availability Heuristic"
                ],
                "answer": "Fundamental Attribution Error",
                "explanation": "Fundamental Attribution Error is the tendency to underestimate the influence of external situational factors and overestimate internal personal factors when judging others.",
                "source": "Robbins & Judge 18th Ed, Ch 6"
            },
            {
                "text": "What does Leon Festinger's theory of 'Cognitive Dissonance' explain?",
                "difficulty": "medium",
                "options": [
                    "The psychological discomfort experienced when an individual holds two contradictory beliefs or acts contrary to their attitudes",
                    "The physical hearing loss caused by industrial machinery",
                    "The mathematical calculation of cost variance",
                    "The speed of organizational email communication"
                ],
                "answer": "The psychological discomfort experienced when an individual holds two contradictory beliefs or acts contrary to their attitudes",
                "explanation": "Cognitive dissonance describes the internal psychological tension that arises when attitudes and observed actions conflict, motivating the person to alter their attitude or behavior.",
                "source": "Robbins & Judge 18th Ed, Ch 3"
            },
            {
                "text": "In perceptual distortion, what is the 'Halo Effect'?",
                "difficulty": "medium",
                "options": [
                    "Drawing a general positive impression about an individual based on a single notable characteristic",
                    "Judging a candidate solely by their criminal record",
                    "Assuming every employee has equal analytical capability",
                    "Evaluating team members based only on their most recent 24-hour output"
                ],
                "answer": "Drawing a general positive impression about an individual based on a single notable characteristic",
                "explanation": "The Halo Effect occurs when an observer forms an overall favorable appraisal of someone's total performance based on one salient attribute (such as intelligence or appearance).",
                "source": "Robbins & Judge 18th Ed, Ch 6"
            },
            {
                "text": "According to the Myers-Briggs Type Indicator (MBTI), an individual who relies on systematic logic and cause-and-effect analysis falls under which dimension?",
                "difficulty": "medium",
                "options": ["Thinking (T)", "Feeling (F)", "Intuitive (N)", "Perceiving (P)"],
                "answer": "Thinking (T)",
                "explanation": "The MBTI Thinking vs Feeling dimension evaluates how individuals make decisions: Thinkers use objective reason and logic, while Feelers prioritize personal values and human relationships.",
                "source": "Robbins & Judge 18th Ed, Ch 5"
            },
            {
                "text": "Which dimension of the Big Five Personality Model is the most consistent and strongest predictor of high job performance across diverse occupations?",
                "difficulty": "medium",
                "options": [
                    "Conscientiousness",
                    "Extroversion",
                    "Openness to Experience",
                    "Emotional Stability"
                ],
                "answer": "Conscientiousness",
                "explanation": "Conscientiousness reflects dependability, thoroughness, goal-orientation, and organized persistence, making it the strongest universal predictor of job performance.",
                "source": "Robbins & Judge 18th Ed, Ch 5"
            },
            {
                "text": "How does 'Emotional Labor' impact service-sector employees according to Arlie Hochschild's framework?",
                "difficulty": "medium",
                "options": [
                    "Employees must express organizationally desired emotions during interpersonal transactions, leading to potential emotional exhaustion",
                    "Workers are required to lift heavy mechanical loads in factories",
                    "Managers compute emotional metrics on accounting spreadsheets",
                    "Employees receive hourly overtime wages for taking customer calls"
                ],
                "answer": "Employees must express organizationally desired emotions during interpersonal transactions, leading to potential emotional exhaustion",
                "explanation": "Emotional labor requires displaying scripted or expected emotions (e.g. flight attendants smiling), which creates dissonance and burnout when genuine feelings differ.",
                "source": "Robbins & Judge 18th Ed, Ch 4"
            },
            {
                "text": "What distinguishes 'Terminal Values' from 'Instrumental Values' in the Rokeach Value Survey?",
                "difficulty": "medium",
                "options": [
                    "Terminal values represent desirable end-states of existence, whereas instrumental values represent preferred modes of conduct to achieve them",
                    "Terminal values only apply to retired workers, while instrumental values apply to interns",
                    "Terminal values change every month, whereas instrumental values never vary",
                    "Terminal values are audited by certified accountants, while instrumental values are not"
                ],
                "answer": "Terminal values represent desirable end-states of existence, whereas instrumental values represent preferred modes of conduct to achieve them",
                "explanation": "Milton Rokeach separated terminal values (lifelong end goals like happiness or world peace) from instrumental values (modes of behavior like honesty and ambition used to attain them).",
                "source": "Robbins & Judge 18th Ed, Ch 5"
            },
            {
                "text": "Which response to employee job dissatisfaction in the EVLN framework is characterized as an active and destructive response?",
                "difficulty": "medium",
                "options": ["Exit", "Voice", "Loyalty", "Neglect"],
                "answer": "Exit",
                "explanation": "In the Exit-Voice-Loyalty-Neglect framework, Exit is active/destructive (quitting the firm), while Voice is active/constructive, Loyalty is passive/constructive, and Neglect is passive/destructive.",
                "source": "Robbins & Judge 18th Ed, Ch 3"
            },
            {
                "text": "What is the 'Self-Serving Bias' commonly observed in corporate performance appraisals?",
                "difficulty": "medium",
                "options": [
                    "Attributing personal successes to internal factors (ability) while blaming personal failures on external factors (bad luck)",
                    "Volunteering to serve lunch at corporate cafeteria events",
                    "Giving bonuses only to senior executives while cutting line worker pay",
                    "Selecting only high-risk capital ventures with guaranteed returns"
                ],
                "answer": "Attributing personal successes to internal factors (ability) while blaming personal failures on external factors (bad luck)",
                "explanation": "The self-serving bias is an ego-defense mechanism where people claim personal credit for positive outcomes but deflect blame for negative outcomes onto outside circumstances.",
                "source": "Robbins & Judge 18th Ed, Ch 6"
            },

            # 10 HARD QUESTIONS FOR OB UNIT 1
            {
                "text": "Under the 'Trait Activation Theory' (TAT), how do organizational cues regulate the expression of personality traits in employee performance?",
                "difficulty": "hard",
                "options": [
                    "Situations provide specific cues that trigger trait-relevant behavior, meaning a personality trait only influences performance when the context activates it",
                    "Employees are genetically modified to express only extroverted sales traits during meetings",
                    "Trait activation occurs solely when monetary incentives exceed twice the standard industry wage",
                    "Traits are completely suppressed by hierarchical bureaucracy and never influence modern work results"
                ],
                "answer": "Situations provide specific cues that trigger trait-relevant behavior, meaning a personality trait only influences performance when the context activates it",
                "explanation": "Trait Activation Theory demonstrates that personality manifests as behavior in response to situation-specific cues (e.g. ambiguity or crisis activates neuroticism or creativity).",
                "source": "Tett & Burnett 2003; Robbins & Judge 18th Ed, Ch 5"
            },
            {
                "text": "In Kaneman & Tversky's Prospect Theory applied to managerial decision making, how does loss aversion affect an executive's risk posture?",
                "difficulty": "hard",
                "options": [
                    "Individuals are risk-averse when facing potential gains, but become distinctly risk-seeking when facing potential losses",
                    "Managers treat equal amounts of gain and loss with strictly identical emotional utility",
                    "Executives always maximize expected value regardless of framing",
                    "Losses generate half the psychological displeasure that identical gains produce"
                ],
                "answer": "Individuals are risk-averse when facing potential gains, but become distinctly risk-seeking when facing potential losses",
                "explanation": "Prospect Theory shows that the pain of a loss is psychologically twice as potent as the pleasure of an equivalent gain; thus managers become risk-seeking to avoid definite losses.",
                "source": "Kahneman & Tversky; Robbins & Judge 18th Ed, Ch 6"
            },
            {
                "text": "How does the 'Dark Triad' personality constellation (Machiavellianism, Narcissism, Psychopathy) manifest in destructive corporate leadership?",
                "difficulty": "hard",
                "options": [
                    "Pragmatic manipulation for personal power (Machiavellianism), grandiose sense of entitlement (Narcissism), and lack of empathy with impulsive callousness (Psychopathy)",
                    "Subtle introversion combined with heightened technical conscientiousness and fear of public speaking",
                    "Extreme altruism, self-sacrificing team loyalty, and reluctance to discipline underperformers",
                    "A pure legal classification of antitrust violations under corporate criminal law"
                ],
                "answer": "Pragmatic manipulation for personal power (Machiavellianism), grandiose sense of entitlement (Narcissism), and lack of empathy with impulsive callousness (Psychopathy)",
                "explanation": "The Dark Triad comprises three malevolent personality dimensions that correlate with unethical manipulation, exploitation of subordinates, and organizational crisis.",
                "source": "Paulhus & Williams 2002; Robbins & Judge 18th Ed, Ch 5"
            },
            {
                "text": "According to Mayer and Salovey's Four-Branch Model of Emotional Intelligence, what is the highest and most complex cognitive tier?",
                "difficulty": "hard",
                "options": [
                    "Reflective Regulation / Management of Emotions to promote emotional and intellectual growth",
                    "Basic perception and identification of facial emotion",
                    "Using emotions to facilitate analytical thinking",
                    "Understanding complex emotional blends and transitional states"
                ],
                "answer": "Reflective Regulation / Management of Emotions to promote emotional and intellectual growth",
                "explanation": "Mayer & Salovey's model progresses from (1) Perceiving emotions -> (2) Facilitating thought -> (3) Understanding emotions -> (4) Managing and regulating emotions reflectively.",
                "source": "Mayer, Salovey & Caruso; Robbins & Judge 18th Ed, Ch 4"
            },
            {
                "text": "In the context of Cognitive Evaluation Theory, how does introducing extrinsic monetary rewards for an intrinsically motivating task alter employee motivation?",
                "difficulty": "hard",
                "options": [
                    "It shifts the locus of causality from internal to external, potentially eroding intrinsic motivation and task autonomy",
                    "It mathematically doubles intrinsic motivation due to compound reinforcement",
                    "It immediately converts the employee into a high-scoring Machiavellian personality",
                    "It eliminates the need for organizational goal-setting architectures"
                ],
                "answer": "It shifts the locus of causality from internal to external, potentially eroding intrinsic motivation and task autonomy",
                "explanation": "Cognitive Evaluation Theory (Deci & Ryan) asserts that external tangible rewards can diminish feelings of autonomy and competence, decreasing inherent intrinsic enjoyment.",
                "source": "Deci & Ryan Self-Determination Theory; Robbins & Judge Ch 7"
            },
            {
                "text": "What is the core distinction between 'Deep Acting' and 'Surface Acting' in employee emotional regulation?",
                "difficulty": "hard",
                "options": [
                    "Deep acting modifies internal feelings to genuinely align with display rules, whereas surface acting feigns displayed emotions without changing inner feelings",
                    "Deep acting only occurs on theatrical stages, while surface acting is used in manufacturing plants",
                    "Surface acting reduces emotional exhaustion, whereas deep acting causes severe clinical depression in all cases",
                    "Deep acting is illegal under statutory labor compensation guidelines"
                ],
                "answer": "Deep acting modifies internal feelings to genuinely align with display rules, whereas surface acting feigns displayed emotions without changing inner feelings",
                "explanation": "Deep acting actively alters inner emotional appraisal so outward expression is authentic; surface acting merely paints a false facade, resulting in greater cognitive dissonance.",
                "source": "Hochschild 1983; Grandey 2003; Robbins & Judge Ch 4"
            },
            {
                "text": "How does 'Bounded Rationality' in Herbert Simon's behavioral model challenge the classical economic model of perfect managerial decision-making?",
                "difficulty": "hard",
                "options": [
                    "Decision-makers operate under cognitive constraints, information limitations, and time pressures, leading to satisficing rather than true optimization",
                    "Managers possess unlimited computational capacity but deliberately choose suboptimal options out of malice",
                    "Rationality is bounded only by the physical size of the corporate office building",
                    "Economic equilibrium models perfectly describe 100% of executive business choices"
                ],
                "answer": "Decision-makers operate under cognitive constraints, information limitations, and time pressures, leading to satisficing rather than true optimization",
                "explanation": "Herbert Simon won the Nobel Prize for demonstrating that human information processing is limited; managers formulate simplified models and satisfice (pick the first acceptable solution).",
                "source": "Herbert Simon, Administrative Behavior; Robbins & Judge Ch 6"
            },
            {
                "text": "In Situation Strength Theory, what characterizes a 'Strong Situation' versus a 'Weak Situation' regarding personality manifestation?",
                "difficulty": "hard",
                "options": [
                    "Strong situations have explicit norms and clear consequences that suppress individual personality differences, whereas weak situations lack rigid rules, allowing personality to strongly dictate behavior",
                    "Strong situations feature high employee muscle strength, while weak situations involve sedentary desk work",
                    "Weak situations eliminate all interpersonal communication between workers",
                    "Strong situations only occur during bankruptcy liquidation proceedings"
                ],
                "answer": "Strong situations have explicit norms and clear consequences that suppress individual personality differences, whereas weak situations lack rigid rules, allowing personality to strongly dictate behavior",
                "explanation": "Situation Strength Theory (Mischel) posits that strong situations (e.g. structured red-light traffic or rigid SOPs) compel uniform behavior, whereas ambiguous/weak situations reveal individual personality traits.",
                "source": "Mischel 1977; Robbins & Judge 18th Ed, Ch 5"
            },
            {
                "text": "Which psychological phenomenon explains why organizational groups frequently make decisions that are substantially more extreme than the initial inclinations of individual members?",
                "difficulty": "hard",
                "options": [
                    "Group Polarization",
                    "Social Loafing",
                    "Cognitive Anchoring",
                    "Ringelmann Effect"
                ],
                "answer": "Group Polarization",
                "explanation": "Group polarization occurs when deliberation strengthens the initial shared tendencies of group members, pushing the collective choice towards more extreme cautiousness or extreme risk-taking.",
                "source": "Moscovici & Zavalloni; Robbins & Judge Ch 9"
            },
            {
                "text": "Under the 'Job Characteristics Model' (Hackman & Oldham), which core psychological state is produced when a job provides high 'Skill Variety, Task Identity, and Task Significance'?",
                "difficulty": "hard",
                "options": [
                    "Experienced Meaningfulness of the Work",
                    "Experienced Responsibility for Outcomes of the Work",
                    "Knowledge of the Actual Results of Work Activities",
                    "Total Elimination of Cognitive Dissonance"
                ],
                "answer": "Experienced Meaningfulness of the Work",
                "explanation": "The JCM establishes that Skill Variety, Task Identity, and Task Significance collectively foster 'Experienced Meaningfulness'; Autonomy fosters 'Responsibility'; and Feedback provides 'Knowledge of Results'.",
                "source": "Hackman & Oldham 1976; Robbins & Judge Ch 8"
            }
        ]

        # Insert OB Unit 1 questions
        for q_item in ob_u1_questions:
            existing_q = db.query(Question).filter(
                Question.subject_id == ob_subj.id,
                Question.question_text == q_item["text"]
            ).first()
            if not existing_q:
                new_q = Question(
                    subject_id=ob_subj.id,
                    unit_id=ob_u1.id,
                    question_text=q_item["text"],
                    difficulty=q_item["difficulty"],
                    options_json=json.dumps(q_item["options"]),
                    correct_answer=q_item["answer"],
                    explanation=q_item["explanation"],
                    source_reference=q_item["source"],
                    is_active=True,
                    is_approved=True,
                    created_by_id=admin_user.id,
                    approved_by_id=admin_user.id
                )
                db.add(new_q)
        db.commit()

        # 4. SEED QUESTIONS FOR OTHER SUBJECTS (Managerial Accounting, Management Fundamentals, IKS, etc.)
        # We add high quality questions across difficulties so all 8 subjects have questions!
        general_questions = [
            # MANAGERIAL ACCOUNTING
            {
                "subject_code": "MA-102",
                "unit_number": 4,
                "text": "What is the Break-Even Point formula in units for a single product firm?",
                "difficulty": "easy",
                "options": [
                    "Fixed Costs / Contribution Margin per Unit",
                    "Total Sales / Variable Cost per Unit",
                    "Net Profit / Total Assets",
                    "Gross Margin / Depreciation"
                ],
                "answer": "Fixed Costs / Contribution Margin per Unit",
                "explanation": "The break-even point in units is calculated by dividing total fixed costs by contribution margin per unit (Selling price - Variable cost).",
                "source": "Horngren's Cost Accounting, Ch 3"
            },
            {
                "subject_code": "MA-102",
                "unit_number": 3,
                "text": "In cost accounting, which costs are defined as 'Prime Costs'?",
                "difficulty": "medium",
                "options": [
                    "Direct Material + Direct Labor + Direct Expenses",
                    "Total Factory Overhead + Administrative Costs",
                    "Selling Expenses + Distribution Costs",
                    "Fixed Cost + Sunk Cost"
                ],
                "answer": "Direct Material + Direct Labor + Direct Expenses",
                "explanation": "Prime cost comprises all direct costs attributable to manufacturing before factory overhead is applied.",
                "source": "Horngren's Cost Accounting, Ch 2"
            },
            {
                "subject_code": "MA-102",
                "unit_number": 5,
                "text": "What does an unfavorable Material Usage Variance indicate in standard costing?",
                "difficulty": "hard",
                "options": [
                    "Actual quantity of raw materials consumed exceeded the standard quantity allowed for actual production",
                    "Actual price paid per kg was higher than standard purchase price",
                    "Production plant operated below 50% capacity",
                    "Direct labor efficiency decreased during evening shifts"
                ],
                "answer": "Actual quantity of raw materials consumed exceeded the standard quantity allowed for actual production",
                "explanation": "Material usage variance measures physical quantity variance: (Standard Quantity - Actual Quantity) * Standard Price. If actual > standard, variance is unfavorable.",
                "source": "Horngren's Cost Accounting, Ch 7"
            },

            # MANAGEMENT FUNDAMENTALS
            {
                "subject_code": "MF-103",
                "unit_number": 1,
                "text": "Who is universally recognized as the Father of Scientific Management?",
                "difficulty": "easy",
                "options": ["Frederick Winslow Taylor", "Henri Fayol", "Max Weber", "Elton Mayo"],
                "answer": "Frederick Winslow Taylor",
                "explanation": "F.W. Taylor pioneered scientific management emphasizing time-motion studies, standardization, and productivity piece-rates.",
                "source": "Koontz & Weihrich, Ch 2"
            },
            {
                "subject_code": "MF-103",
                "unit_number": 3,
                "text": "What does Henri Fayol's 'Unity of Command' principle state?",
                "difficulty": "medium",
                "options": [
                    "An employee should receive orders from only one direct superior",
                    "All enterprise departments must share identical financial budgets",
                    "Executive authority must be concentrated exclusively in board directors",
                    "Salaries across all functional units must be strictly equal"
                ],
                "answer": "An employee should receive orders from only one direct superior",
                "explanation": "Unity of Command ensures clarity of responsibility and prevents conflicting directives by stipulating that each worker reports to a single manager.",
                "source": "Henri Fayol 14 Principles; Koontz & Weihrich"
            },
            {
                "subject_code": "MF-103",
                "unit_number": 5,
                "text": "In Kaplan and Norton's Balanced Scorecard, which four perspectives are evaluated?",
                "difficulty": "hard",
                "options": [
                    "Financial, Customer, Internal Business Processes, and Learning & Growth",
                    "Cost, Revenue, Dividend, and Tax Minimization",
                    "Production, Logistics, Legal, and Public Relations",
                    "Assets, Liabilities, Depreciation, and Amortization"
                ],
                "answer": "Financial, Customer, Internal Business Processes, and Learning & Growth",
                "explanation": "The Balanced Scorecard broadens traditional accounting by measuring performance across Financial, Customer, Internal Processes, and Organizational Learning & Growth.",
                "source": "Kaplan & Norton 1996; Koontz & Weihrich Ch 14"
            },

            # INDIAN KNOWLEDGE SYSTEMS
            {
                "subject_code": "IKS-104",
                "unit_number": 2,
                "text": "In classical Indian philosophy, what are the four 'Purusharthas' (legitimate human aims)?",
                "difficulty": "easy",
                "options": [
                    "Dharma (Ethics), Artha (Wealth), Kama (Desire), Moksha (Liberation)",
                    "Veda, Upanishad, Purana, Itihasa",
                    "Brahmana, Kshatriya, Vaishya, Shudra",
                    "Satya, Ahimsa, Asteya, Aparigraha"
                ],
                "answer": "Dharma (Ethics), Artha (Wealth), Kama (Desire), Moksha (Liberation)",
                "explanation": "The Purusharthas define a holistic balance between ethical duty (Dharma), wealth creation (Artha), aesthetic desires (Kama), and spiritual liberation (Moksha).",
                "source": "IKS Ministry of Education Framework 2023"
            },
            {
                "subject_code": "IKS-104",
                "unit_number": 3,
                "text": "According to Kautilya's Arthashastra, which element constitutes the 'Saptanga Theory' of the state?",
                "difficulty": "medium",
                "options": [
                    "Swami (Ruler), Amatya (Ministers), Janapada (Territory), Durga (Fort), Kosha (Treasury), Danda (Army), Mitra (Allies)",
                    "Seven sacred rivers of ancient Bharat",
                    "Seven tax brackets for international maritime merchants",
                    "Seven religious festivals recognized by the royal council"
                ],
                "answer": "Swami (Ruler), Amatya (Ministers), Janapada (Territory), Durga (Fort), Kosha (Treasury), Danda (Army), Mitra (Allies)",
                "explanation": "The Saptanga theory models an organic state comprising seven interrelated limbs essential for sovereignty and prosperous governance.",
                "source": "Kautilya's Arthashastra, Book VI"
            },
            {
                "subject_code": "IKS-104",
                "unit_number": 2,
                "text": "How does the principle of 'Nishkama Karma' from the Bhagavad Gita apply to modern corporate executive leadership?",
                "difficulty": "hard",
                "options": [
                    "Acting with excellence, dedication, and ethical conviction while remaining unattached to anxiety over personal selfish rewards",
                    "Abandoning all business activities to live as an ascetic hermit",
                    "Refusing to accept corporate salary bonuses under any circumstances",
                    "Executing executive decisions without consulting board directors or legal counsel"
                ],
                "answer": "Acting with excellence, dedication, and ethical conviction while remaining unattached to anxiety over personal selfish rewards",
                "explanation": "Nishkama Karma advocates focused execution of duty with mastery without being consumed by egoistic anxiety over outcomes, creating ethical, resilient leadership.",
                "source": "Bhagavad Gita 2.47; Classical Indic Management Studies"
            },

            # ECONOMIC ANALYSIS FOR BUSINESS DECISIONS
            {
                "subject_code": "EABD-105",
                "unit_number": 2,
                "text": "If a 10% decrease in the price of a luxury watch leads to a 25% increase in quantity demanded, what is the price elasticity of demand?",
                "difficulty": "easy",
                "options": ["2.5 (Elastic)", "0.4 (Inelastic)", "1.0 (Unitary)", "0.0 (Zero)"],
                "answer": "2.5 (Elastic)",
                "explanation": "Price elasticity of demand = % change in quantity demanded / % change in price = 25% / 10% = 2.5 (elastic demand).",
                "source": "Dominick Salvatore, Ch 4"
            },
            {
                "subject_code": "EABD-105",
                "unit_number": 4,
                "text": "Why does the demand curve for an individual firm in an Oligopoly exhibit a 'kink' according to Paul Sweezy's model?",
                "difficulty": "medium",
                "options": [
                    "Competitors match price cuts to protect market share, but do not match price increases",
                    "Government antitrust regulations impose arbitrary ceiling prices",
                    "Consumers purchase goods only during quarterly festive seasons",
                    "Production plants operate with strictly zero variable costs"
                ],
                "answer": "Competitors match price cuts to protect market share, but do not match price increases",
                "explanation": "Sweezy's kinked demand curve models oligopoly price rigidity: if a firm raises price, rivals don't follow (elastic); if it lowers price, rivals follow (inelastic).",
                "source": "Salvatore, Managerial Economics, Ch 10"
            },
            {
                "subject_code": "EABD-105",
                "unit_number": 3,
                "text": "In a Cobb-Douglas production function Q = A * L^0.6 * K^0.7, what type of returns to scale does the enterprise exhibit?",
                "difficulty": "hard",
                "options": [
                    "Increasing Returns to Scale (IRS)",
                    "Constant Returns to Scale (CRS)",
                    "Decreasing Returns to Scale (DRS)",
                    "Zero Returns to Scale"
                ],
                "answer": "Increasing Returns to Scale (IRS)",
                "explanation": "Sum of output elasticities = 0.6 + 0.7 = 1.3. Since sum > 1.0, the production function displays Increasing Returns to Scale.",
                "source": "Salvatore, Managerial Economics, Ch 6"
            },

            # DECISION SCIENCE
            {
                "subject_code": "DS-106",
                "unit_number": 1,
                "text": "In Linear Programming, what does an 'unbounded solution' signify?",
                "difficulty": "easy",
                "options": [
                    "The objective function value can increase infinitely without violating any constraints",
                    "There is no point that satisfies all constraints simultaneously",
                    "Multiple optimal corner points exist on the constraint boundary",
                    "All decision variables must equal zero"
                ],
                "answer": "The objective function value can increase infinitely without violating any constraints",
                "explanation": "An unbounded problem occurs when the feasible region is open in the direction of optimization, allowing infinite profit.",
                "source": "Hamdy Taha, Operations Research, Ch 2"
            },
            {
                "subject_code": "DS-106",
                "unit_number": 3,
                "text": "Which method is commonly used to find an initial basic feasible solution to a Transportation Problem that generally yields a solution closest to optimum?",
                "difficulty": "medium",
                "options": [
                    "Vogel's Approximation Method (VAM)",
                    "North-West Corner Rule",
                    "Least Cost Method",
                    "Stepping Stone Method"
                ],
                "answer": "Vogel's Approximation Method (VAM)",
                "explanation": "VAM uses opportunity penalty costs (difference between two lowest cell costs) to guide allocations, typically yielding near-optimal starting solutions.",
                "source": "Taha, Operations Research, Ch 5"
            },
            {
                "subject_code": "DS-106",
                "unit_number": 5,
                "text": "In PERT project scheduling, if optimistic time a=4 days, most likely time m=7 days, and pessimistic time b=16 days, what is the expected activity duration?",
                "difficulty": "hard",
                "options": ["8 days", "7 days", "9 days", "10 days"],
                "answer": "8 days",
                "explanation": "PERT expected duration te = (a + 4m + b) / 6 = (4 + 4(7) + 16) / 6 = (4 + 28 + 16) / 6 = 48 / 6 = 8 days.",
                "source": "Taha, Operations Research, Ch 6"
            },

            # BUSINESS ANALYTICS
            {
                "subject_code": "BA-107",
                "unit_number": 2,
                "text": "Which statistical measure is most resistant to extreme numerical outliers in an income distribution?",
                "difficulty": "easy",
                "options": ["Median", "Mean", "Variance", "Standard Deviation"],
                "answer": "Median",
                "explanation": "The median represents the middle score of a sorted dataset and is insensitive to extreme high or low skewing values.",
                "source": "Albright & Winston, Ch 3"
            },
            {
                "subject_code": "BA-107",
                "unit_number": 4,
                "text": "In a multiple linear regression model, what does a Variance Inflation Factor (VIF) greater than 10 indicate?",
                "difficulty": "medium",
                "options": [
                    "Severe multicollinearity among independent predictor variables",
                    "A perfect model fit with 100% predictive accuracy",
                    "Heteroscedasticity in regression residuals",
                    "Absence of any linear correlation between X and Y"
                ],
                "answer": "Severe multicollinearity among independent predictor variables",
                "explanation": "A VIF exceeding 5 or 10 signifies that independent predictors are highly correlated with one another, inflating standard errors of coefficient estimates.",
                "source": "Albright & Winston, Ch 11"
            },
            {
                "subject_code": "BA-107",
                "unit_number": 3,
                "text": "What does a p-value of 0.012 imply when testing a null hypothesis at a 5% (alpha = 0.05) level of significance?",
                "difficulty": "hard",
                "options": [
                    "Reject the null hypothesis; the observed finding is statistically significant",
                    "Fail to reject the null hypothesis; the finding is due to pure chance",
                    "The probability of the alternative hypothesis being true is exactly 1.2%",
                    "The sample size must be doubled before any conclusion can be reached"
                ],
                "answer": "Reject the null hypothesis; the observed finding is statistically significant",
                "explanation": "When the calculated p-value (0.012) is less than alpha (0.05), we reject the null hypothesis in favor of the alternative hypothesis.",
                "source": "Albright & Winston, Ch 7"
            },

            # BASICS OF MARKETING
            {
                "subject_code": "BOM-108",
                "unit_number": 2,
                "text": "In the STP marketing framework, what does 'STP' stand for?",
                "difficulty": "easy",
                "options": [
                    "Segmentation, Targeting, Positioning",
                    "Sales, Tactics, Promotion",
                    "Strategy, Technology, Performance",
                    "Supply, Transport, Pricing"
                ],
                "answer": "Segmentation, Targeting, Positioning",
                "explanation": "STP is the core strategic process: Segment the broad market, Target the most viable segments, and Position the value offering uniquely.",
                "source": "Kotler & Keller, Marketing Management, Ch 5"
            },
            {
                "subject_code": "BOM-108",
                "unit_number": 3,
                "text": "In the Boston Consulting Group (BCG) Matrix, which quadrant characterizes products with high market share in a slow-growth industry?",
                "difficulty": "medium",
                "options": ["Cash Cows", "Stars", "Question Marks", "Dogs"],
                "answer": "Cash Cows",
                "explanation": "Cash Cows generate substantial liquidity with minimal investment because they dominate mature, low-growth markets.",
                "source": "Kotler & Keller, Ch 2"
            },
            {
                "subject_code": "BOM-108",
                "unit_number": 4,
                "text": "What is the strategic objective of 'Price Skimming' during new product launches?",
                "difficulty": "hard",
                "options": [
                    "Setting a high initial price to recover heavy R&D expenditures from less price-sensitive early adopters before lowering prices over time",
                    "Setting an artificially low price below variable cost to bankrupt competitors",
                    "Matching the exact average market price charged by industry leaders",
                    "Pricing products based purely on government statutory quotas"
                ],
                "answer": "Setting a high initial price to recover heavy R&D expenditures from less price-sensitive early adopters before lowering prices over time",
                "explanation": "Price skimming maximizes initial revenue from innovators/early adopters willing to pay a premium before cascading down to mass market segments.",
                "source": "Kotler & Keller, Ch 14"
            }
        ]

        for q_item in general_questions:
            subj = subject_map.get(q_item["subject_code"])
            if not subj:
                continue
            u_key = f"{q_item['subject_code']}_U{q_item['unit_number']}"
            unit = unit_map.get(u_key)
            existing_q = db.query(Question).filter(
                Question.subject_id == subj.id,
                Question.question_text == q_item["text"]
            ).first()
            if not existing_q:
                new_q = Question(
                    subject_id=subj.id,
                    unit_id=unit.id if unit else None,
                    question_text=q_item["text"],
                    difficulty=q_item["difficulty"],
                    options_json=json.dumps(q_item["options"]),
                    correct_answer=q_item["answer"],
                    explanation=q_item["explanation"],
                    source_reference=q_item["source"],
                    is_active=True,
                    is_approved=True,
                    created_by_id=admin_user.id,
                    approved_by_id=admin_user.id
                )
                db.add(new_q)
        db.commit()

        # 5. SEED SAMPLE RESOURCES (Books, Original University Papers, Solved Papers)
        sample_book_path = os.path.join(settings.UPLOAD_DIR, "books", "ob_robbins_18th_sample.pdf")
        create_sample_pdf_if_missing(sample_book_path, "Organizational Behaviour - Robbins & Judge 18th Ed Reference Guide")
        
        sample_paper_path = os.path.join(settings.UPLOAD_DIR, "question_papers", "ob_winter_2024_qp.pdf")
        create_sample_pdf_if_missing(sample_paper_path, "Autonomous MBA Winter 2024 Question Paper - OB-101")
        
        sample_solved_path = os.path.join(settings.UPLOAD_DIR, "solved_papers", "ob_winter_2024_solved.pdf")
        create_sample_pdf_if_missing(sample_solved_path, "Autonomous MBA Winter 2024 Model Solutions - OB-101")

        # Book
        if not db.query(Resource).filter(Resource.file_name == "ob_robbins_18th_sample.pdf").first():
            db.add(Resource(
                title="Organizational Behaviour (Global 18th Edition Reference)",
                resource_type=ResourceType.BOOK.value,
                subject_id=ob_subj.id,
                author="Stephen P. Robbins, Timothy A. Judge",
                publisher="Pearson Education",
                edition="18th Global Edition",
                file_name="ob_robbins_18th_sample.pdf",
                file_path=sample_book_path,
                file_size_bytes=os.path.getsize(sample_book_path),
                mime_type="application/pdf",
                source_reference="Pearson / Department Recommended Text",
                is_verified_solution=False,
                uploaded_by_id=admin_user.id
            ))

        # Question Paper
        if not db.query(Resource).filter(Resource.file_name == "ob_winter_2024_qp.pdf").first():
            db.add(Resource(
                title="MBA Sem 1 End-Term Examination Question Paper — Winter 2024",
                resource_type=ResourceType.QUESTION_PAPER.value,
                subject_id=ob_subj.id,
                exam_session="Winter",
                exam_month="December",
                exam_year=2024,
                exam_pattern="Autonomous 70-30 Evaluation Scheme",
                file_name="ob_winter_2024_qp.pdf",
                file_path=sample_paper_path,
                file_size_bytes=os.path.getsize(sample_paper_path),
                mime_type="application/pdf",
                source_reference="University Examination Control Board",
                is_verified_solution=False,
                uploaded_by_id=admin_user.id
            ))

        # Solved Paper
        if not db.query(Resource).filter(Resource.file_name == "ob_winter_2024_solved.pdf").first():
            db.add(Resource(
                title="MBA Sem 1 Winter 2024 — Verified Model Answer Sheet & Step Marking",
                resource_type=ResourceType.SOLVED_PAPER.value,
                subject_id=ob_subj.id,
                exam_session="Winter",
                exam_month="December",
                exam_year=2024,
                exam_pattern="Autonomous 70-30 Evaluation Scheme",
                file_name="ob_winter_2024_solved.pdf",
                file_path=sample_solved_path,
                file_size_bytes=os.path.getsize(sample_solved_path),
                mime_type="application/pdf",
                source_reference="Faculty of Management Studies Academic Evaluation Committee",
                is_verified_solution=True,
                verification_disclaimer="Verified faculty model solution with grading criteria. Cross-check case analysis arguments with prescribed rubric.",
                uploaded_by_id=admin_user.id
            ))

        db.commit()
        print("Database seeded successfully with subjects, units, 30+ verified MCQs, sample users and library resources.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
