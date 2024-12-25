import calendar
import datetime
import random
import xml.etree.ElementTree as ElementTree

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_user, logout_user

from .extenstions import db, login_manager
from .models import (
    Blog,
    Course,
    CourseGroup,
    Event,
    Feedback,
    Registration,
    Staff,
    Teacher,
    Timetable,
    Toefl,
    ToeflRegistration,
    User,
)

main = Blueprint("main", __name__)


def parse_editorjs(json_data):
    if json_data is None:
        return "No content available."
    blocks = json_data.get("blocks")
    if blocks is not None:
        html_list = []
        for block in blocks:
            block_html = ""
            block_type = block.get("type")
            if block_type == "paragraph":
                block_html = f"<p>{block.get('data').get('text')}</p>"
            elif block_type == "header":
                level = block.get("data").get("level")
                text = block.get("data").get("text")
                block_html = f"<h{level} id='{text.replace("'", "")}'>{text}</h{level}>"
            elif block_type == "list":
                style = block.get("data").get("style")
                if style == "ordered":
                    block_html = f"<ol class='list-decimal'>{''.join([f'<li>{item}</li>' for item in block.get('data').get('items')])}</ol>"
                else:
                    block_html = f"<ul class='list-disc'>{''.join([f'<li>{item}</li>' for item in block.get('data').get('items')])}</ul>"
            elif block_type == "embed":
                caption = block.get("data").get("caption")
                block_html = f"<figure><iframe class='w-full aspect-video' src='{block.get("data").get("embed")}' frameborder='0' allow='autoplay; fullscreen; picture-in-picture' allowfullscreen></iframe><figcaption class='text-center'>{caption}</figcaption></figure>"
            elif block_type == "quote":
                alignment = block.get("data").get("alignment")
                block_html = f"<blockquote {"class='text-center text-pretty'" if alignment == 'center' else ''}>{block.get("data").get("text")}</blockquote>"
            elif block_type == "linkblock":
                block_html = f"<a href='{block.get('data').get('link')}' target='_blank'>{block.get('data').get('meta').get('title')}</a>"
            elif block_type == "image":
                try:
                    picture_url = block.get("data").get("file").get("url")
                    caption = block.get("data").get("caption")
                    with_border = block.get("data").get("withBorder")
                    with_background = block.get("data").get("withBackground")
                    stretched = block.get("data").get("stretched")
                    consolidated_styles = f"{'border border-solid' if with_border else ''} {'w-full' if stretched else ''}"
                    block_html = f"<figure {'class=bg-auto bg-slate-500' if with_background else ''}> <img class='{consolidated_styles} rounded-md' src='{picture_url}'><figcaption class='text-center'>{caption}</figcaption></figure>"
                except Exception as e:
                    print(e)
            elif block_type == "delimiter":
                block_html = "<div class='inline-block text-2xl leading-16 h-8 tracking-wider text-center'>***</div>"
            elif block_type == "code":
                block_html = f"<pre><code>{block.get('data').get('code')}</code></pre>"
            html_list.append(block_html)

    return "".join(html_list)


def generate_month_matrix(month: int, year: int) -> dict:
    month_data = {"month": month, "year": year, "matrix": []}
    month_calendar = calendar.monthcalendar(year, month)

    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
    all_events = Event.get_by_date_range(start_date, end_date)

    for week in month_calendar:
        week_matrix = []
        for day in week:
            if day == 0:
                week_matrix.append({"day": "", "events": []})
            else:
                date = datetime.date(year, month, day)
                event_colors = list(
                    {
                        event_color
                        for event, event_color in all_events
                        if event.date == date
                    }
                )[0:3]
                week_matrix.append({"day": day, "events": event_colors})
        month_data["matrix"].append(week_matrix)
    return month_data


@login_manager.user_loader
def load_user(user_id: int) -> User | None:
    user = User.get_by_id(id=int(user_id))
    if user:
        return user

    return None


@main.route("/lang/<lang>")
def set_lang(lang=None):
    session["lang"] = lang
    return redirect(url_for("main.index"))


@main.route("/")
def index():
    success = None
    if args := request.args:
        success = True if args.get("success") == "true" else False

    course_groups = CourseGroup.get_all()
    feedbacks = Feedback.get_all_verified()
    blogs = Blog.get_all_published()
    hero_list = [
        "hero-1.jpg",
        "hero-2.jpg",
        "hero-3.jpg",
        "hero-4.jpg",
        "hero-5.jpg",
        "hero-6.jpg",
        "hero-7.jpg",
        "hero-8.jpg",
        "hero-9.jpg",
        "hero-10.jpg",
        "hero-11.jpg",
        "hero-12.jpg",
        "hero-13.jpg",
        "hero-14.jpg",
        "hero-15.jpg",
        "hero-16.jpg",
    ]
    random_hero = random.choice(hero_list)

    return render_template(
        "index.html",
        course_groups=course_groups,
        feedbacks=feedbacks,
        random_hero=random_hero,
        success=success,
        blogs=blogs,
    )


@main.route("/courses")
def courses():
    courses = Course.get_all()

    return render_template(
        "courses.html",
        courses=courses,
        course_group=None,
        course_groups=CourseGroup.get_all(),
        course_group_name=None,
    )


@main.route("/courses/<course_group_slug>")
def course_group(course_group_slug: str):
    course_group = (
        CourseGroup.get_by_slug(course_group_slug) if course_group_slug else None
    )
    courses = Course.get_by_course_group_id(course_group.id if course_group else None)

    return render_template(
        "courses.html",
        courses=courses,
        course_group=course_group,
        course_groups=CourseGroup.get_all(),
        course_group_name=course_group_slug,
    )


@main.route("/course/<course_name>")
def course(course_name):
    success = None
    if args := request.args:
        success = True if args.get("success") == "true" else False

    course = Course.get_by_slug(course_name)
    if not course:
        return redirect(url_for("main.courses"))
    timetables = Timetable.get_by_course_id(course.id)

    return render_template(
        "course.html",
        course=course,
        timetables=timetables,
        success=success,
    )


@main.route("/calendar/<int:month>/<int:year>")
def send_calendar(month, year):
    return jsonify(generate_month_matrix(month=month, year=year))


@main.route("/about")
def about():
    staff = Staff.get_all()
    return render_template("about.html", staff=staff)


@main.route("/teachers")
def teachers():
    teachers = Teacher.get_all()
    return render_template("teachers.html", teachers=teachers)


@main.route("/events/<int:month>/<int:year>")
def send_events(month, year):
    events = Event.get_by_month(month, year)
    events_serialized = []
    for event, event_color in events:
        events_serialized.append(
            {
                "name": event.name,
                "description": event.description,
                "event_color": event_color,
                "date": str(event.date),
                "date_string": event.date_string,
            }
        )
    return jsonify(events_serialized)


@main.route("/toefl")
def toefl():
    if (date_str := request.args.get("date", type=str)) != "None" and date_str != None:
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            human_date = date.strftime("%d %B, %Y")
            results = Toefl.get_all_by_date(date)
        except ValueError:
            date = datetime.date.today()
            human_date = date.strftime("%d %B, %Y")
            results = Toefl.get_latest_results()
    else:
        results = Toefl.get_latest_results()
        date = results[0].date if results else datetime.date.today()
        human_date = date.strftime("%d %B, %Y")

    pagination = Toefl.get_pagination_dates(date)
    return render_template(
        "toefl.html", human_date=human_date, results=results, pagination=pagination
    )


def get_available_dates():
    today = datetime.date.today()

    days_until_monday = (0 - today.weekday() + 7) % 7
    days_until_thursday = (3 - today.weekday() + 7) % 7

    next_monday = today + datetime.timedelta(days=days_until_monday)
    next_next_monday = next_monday + datetime.timedelta(days=7)

    next_thursday = today + datetime.timedelta(days=days_until_thursday)
    next_next_thursday = next_thursday + datetime.timedelta(days=7)

    months_ru = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }

    available_dates = [
        {
            "date": f"Понедельник, {months_ru[next_monday.month]} {next_monday.day}, {next_monday.year}",
            "value": next_monday,
        },
        {
            "date": f"Понедельник, {months_ru[next_next_monday.month]} {next_next_monday.day}, {next_next_monday.year}",
            "value": next_next_monday,
        },
        {
            "date": f"Четверг, {months_ru[next_thursday.month]} {next_thursday.day}, {next_thursday.year}",
            "value": next_thursday,
        },
        {
            "date": f"Четверг, {months_ru[next_next_thursday.month]} {next_next_thursday.day}, {next_next_thursday.year}",
            "value": next_next_thursday,
        },
    ]
    available_dates = sorted(available_dates, key=lambda x: x["value"])
    return available_dates


@main.get("/toefl/register")
def toefl_register():
    success = None
    if args := request.args:
        success = True if args.get("success") == "true" else False

    available_dates = get_available_dates()

    return render_template(
        "toefl_register.html", success=success, available_dates=available_dates
    )


@main.post("/toefl/register")
def toefl_register_post():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    day = request.form.get("day")

    if not first_name or not last_name or not email or not phone or not day:
        return redirect(url_for("main.toefl_register", success="false"))

    day = datetime.datetime.strptime(day, "%Y-%m-%d").date()

    try:
        registration = ToeflRegistration(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date=day,
            created_at=datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=6))
            ),
        )
        db.session.add(registration)
        db.session.commit()
    except Exception as e:
        print(e)
        return redirect(url_for("main.toefl_register", success="false"))

    return redirect(url_for("main.toefl_register", success="true"))


@main.post("/register")
def register():
    name = request.form.get("name")
    phone = request.form.get("phone")
    age = request.form.get("age", type=int)
    course_info = request.form.get("course_info")

    if not name or not phone or not age or not course_info:
        return redirect(
            url_for("main.index", _anchor="registration-form", success="false")
        )

    try:
        registration = Registration(
            name=name,
            phone=phone,
            age=age,
            course_info=course_info,
            created_at=datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=6))
            ),
        )
        db.session.add(registration)
        db.session.commit()
    except Exception as e:
        print(e)
        return redirect(
            url_for("main.index", _anchor="registration-form", success="false")
        )

    return redirect(url_for("main.index", _anchor="registration-form", success="true"))


@main.post("/register-course")
def register_course():
    name = request.form.get("name")
    phone = request.form.get("phone")
    age = request.form.get("age", type=int)
    course_info = request.form.get("course_info")

    if not name or not phone or not age or not course_info:
        return redirect(f"{request.referrer}?success=false")

    try:
        registration = Registration(
            name=name,
            phone=phone,
            age=age,
            course_info=course_info,
            created_at=datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=6))
            ),
        )
        db.session.add(registration)
        db.session.commit()
    except Exception as e:
        print(e)
        return redirect(f"{request.referrer}?success=false")

    return redirect(f"{request.referrer}?success=true")


@main.get("/blogs")
def blogs():
    blogs = Blog.get_all_published()
    return render_template("blogs.html", blogs=blogs)


@main.get("/blogs/<blog_slug>")
def blog(blog_slug):
    blog = Blog.get_by_slug(blog_slug)
    if not blog:
        return redirect(url_for("main.index"))
    blog_html = parse_editorjs(blog.json)
    return render_template("blog.html", blog_html=blog_html, blog=blog)


@main.get("/login")
def login():
    return render_template("login.html")


@main.post("/login")
def login_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    user = User.get_by_username(username)
    if user and user.password == password and user.is_admin:
        login_user(user)
        return redirect(url_for("admin.applications"))
    return redirect(url_for("main.login"))


@main.get("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/sitemap.xml")
def sitemap():
    pages = []
    one_day_ago = (
        (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
    )

    # Add static pages
    for rule in current_app.url_map.iter_rules():
        if (
            rule.methods
            and "GET" in rule.methods
            and len(rule.arguments) == 0
            and not rule.rule.startswith("/admin")
            and not rule.rule.startswith("/logout")
            and not rule.rule.startswith("/login")
            and not rule.rule.startswith("/health")
            and not rule.rule.startswith("/lang")
        ):
            pages.append([rule.rule, one_day_ago])

    courses = Course.get_all()
    for course in courses:
        pages.append([f"/course/{course.slug}", one_day_ago])

    course_groups = CourseGroup.get_all()
    for course_group in course_groups:
        pages.append(
            [
                f"/courses/{course_group.slug}",
                one_day_ago,
            ]
        )

    blogs = Blog.get_all_published()
    for blog in blogs:
        pages.append([f"/blogs/{blog.slug}", one_day_ago])

    root = ElementTree.Element(
        "urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    )
    for page in pages:
        url = ElementTree.SubElement(root, "url")
        loc = ElementTree.SubElement(url, "loc")
        loc.text = "https://mldc.auca.kg" + page[0]
        lastmod = ElementTree.SubElement(url, "lastmod")
        lastmod.text = page[1]
        changefreq = ElementTree.SubElement(url, "changefreq")
        changefreq.text = "daily"
        priority = ElementTree.SubElement(url, "priority")
        priority.text = "1.0"

    sitemap_xml = ElementTree.tostring(root, encoding="utf-8")
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response


@main.route("/robots.txt")
def robots():
    robots_txt = "User-agent: *\nDisallow: /admin\nDisallow: /logout\nDisallow: /login\nDisallow: /lang/*\n\nSitemap: https://mldc.auca.kg/sitemap.xml"
    response = make_response(robots_txt)
    response.headers["Content-Type"] = "text/plain"
    return response


@main.get("/health")
def health():
    return "OK"
