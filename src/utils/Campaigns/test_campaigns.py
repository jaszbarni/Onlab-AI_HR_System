import random
import streamlit as st

from classes.form_template_class import FormTemplate
from utils.common import get_user_name
from Database.employee import get_all_employees
from Database.forms import create_form, add_question, create_form_from_template, get_assignments_by_form, update_assignment_status
from Database.campaign import create_campaign
from Database.form_response import add_form_assignments


def generate_test_campaign():
    """Generate a test template with predefined questions, campaign, and responses."""
    employees = get_all_employees()
    user_name = get_user_name()
    
    if not employees:
        st.warning("Nincs munkatárs a rendszerben. Kérlek, először generálj teszt felhasználókat.")
        return

    template_name = "Vezetői Teljesítményértékelő Sablon"
    template_description = "Automatikusan generált teszt sablon vezetői kompetenciák értékelésére."
    
    template_id = create_form(template_name, template_description, user_name, is_template=False)
    
    q1_title = "Stratégiai szemlélet, üzleti gondolkodás"
    q1_desc = """
    Érti, mitől lehet sikeres a cég és a saját divíziója,
    Felismeri az üzleti lehetőségeket, kockázatokat,
    Képes a stratégiai célokat konkrét, megvalósítható lépésekre bontani,
    Összehangolja a saját területét a szervezeti célokkal.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q1_title, q1_desc, "0-5 Rating", 0, 5)
    
    q2_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q2_title, None, "Text Box", None, None)

    q3_title = "Változáskezelés és innováció"
    q3_desc = """
    Nyitott az új ötletekre, fejlesztési javaslatokra,
    Képes a változások bevezetését tervezetten és kommunikáltan végig vinni,
    Innovatív,
    Részt vesz az új eljárások, rendszerek bevezetésében.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q3_title, q3_desc, "0-5 Rating", 0, 5)
    
    q4_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q4_title, None, "Text Box", None, None)

    q5_title = "Csapatirányítás és motiváció"
    q5_desc = """
    Felismeri és fejleszti a munkatársak képességeit,
    Megfelelően motiválja a csapat tagjait,
    Támogató és konstruktív munkahelyi légkört teremt,
    Képes kezelni a csapaton belüli konfliktusokat.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q5_title, q5_desc, "0-5 Rating", 0, 5)
    
    q6_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q6_title, None, "Text Box", None, None)

    q7_title = "Döntéshozatal és problémamegoldás"
    q7_desc = """
    Időben és határozottan hoz meg nehéz döntéseket is,
    A döntések meghozatala előtt megfelelően tájékozódik,
    Proaktív a felmerülő problémák azonosításában és kezelésében,
    Vállalja a felelősséget a meghozott döntésekért.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q7_title, q7_desc, "0-5 Rating", 0, 5)
    
    q8_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q8_title, None, "Text Box", None, None)

    q9_title = "Kommunikáció és visszajelzés"
    q9_desc = """
    Világosan és egyértelműen fogalmazza meg az elvárásokat,
    Rendszeres és építő jellegű visszajelzést ad a munkatársaknak,
    Értő figyelemmel hallgatja meg mások véleményét,
    Hatékonyan kommunikál a társosztályokkal és a vezetőséggel.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q9_title, q9_desc, "0-5 Rating", 0, 5)
    
    q10_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q10_title, None, "Text Box", None, None)

    q11_title = "Eredményorientáltság és felelősségvállalás"
    q11_desc = """
    Fókuszban tartja a kitűzött célok elérését,
    Következetes a minőségi munkavégzés megkövetelésében,
    Felelősséget vállal a saját és a csapata munkájáért,
    Példamutatással jár elöl a mindennapi feladatokban.

    Véleményem szerint kollégám ezen a területen nyújtott teljesítménye:
    """
    add_question(template_id, q11_title, q11_desc, "0-5 Rating", 0, 5)
    
    q12_title = " Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template_id, q12_title, None, "Text Box", None, None)
    
    # Create a second template for Peer evaluation
    template2_name = "Munkatársi Teljesítményértékelő Sablon"
    template2_description = "Automatikusan generált teszt sablon munkatársi kompetenciák értékelésére."
    template2_id = create_form(template2_name, template2_description, user_name, is_template=False)
    
    q1_t2_title = "Csapatmunka és együttműködés"
    q1_t2_desc = "Aktívan részt vesz a közös feladatokban, segíti és támogatja a kollégákat."
    add_question(template2_id, q1_t2_title, q1_t2_desc, "0-5 Rating", 0, 5)
    
    q2_t2_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template2_id, q2_t2_title, None, "Text Box", None, None)
    
    q3_t2_title = "Megbízhatóság és precizitás"
    q3_t2_desc = "Határidőre és a megfelelő minőségben végzi el a rábízott feladatokat."
    add_question(template2_id, q3_t2_title, q3_t2_desc, "0-5 Rating", 0, 5)
    
    q4_t2_title = "Az értékelés rövid indoklása (erősségek, gyengeségek)"
    add_question(template2_id, q4_t2_title, None, "Text Box", None, None)
    
    # Create a Campaign and instantiate a Form from the Template
    campaign_id = create_campaign("Példa Kampány Mindenkinek", "Teszt kampány az AI értékeléshez - Teljes szervezet", user_name)
    form_id = create_form_from_template(template_id, campaign_id, user_name)
    form2_id = create_form_from_template(template2_id, campaign_id, user_name)
    
    form1_obj = FormTemplate(form_id)
    form1_qs = form1_obj.get_questions()
    
    form2_obj = FormTemplate(form2_id)
    form2_qs = form2_obj.get_questions()

    send_form = []
    responses_to_submit = []
    n = len(employees)

    def get_emp_name(idx):
        emp = employees[idx % n]
        return f"{emp['first_name']} {emp['last_name']}"

    good_texts = [
        "Kiváló munkát végez, stratégiai látásmódja és problémamegoldó képessége kiemelkedő. Példamutató kolléga.",
        "Mindig megbízható és precíz. A csapat egyik legértékesebb tagja, aki proaktívan áll a kihívásokhoz.",
        "Inspiráló személyiség, aki képes a legnehezebb helyzetekben is motiválni a környezetét. Kiváló eredményeket hoz.",
        "Nagyon jó szakember, a projektjeit mindig időre és magas minőségben szállítja.",
        "Rendkívül együttműködő, a kommunikációja tiszta és érthető. Öröm vele együtt dolgozni."
    ]
    
    bad_texts = [
        "Sajnos a határidőket ritkán tartja be, a kommunikációja pedig sokszor elmarad az elvárttól. A csapatmunkához való hozzáállása javítandó.",
        "Gyakran pontatlan a munkája, és a kritikát nehezen fogadja. Fejlődnie kell a feladatok priorizálásában.",
        "A csapaton belüli konfliktusok gyakran vezethetők vissza a nem megfelelő kommunikációjára. Motiválatlan benyomást kelt.",
        "Többször előfordult, hogy a rábízott feladatokat nem fejezte be időre, ami a többiek munkáját is hátráltatta.",
        "Nem mutat kellő önállóságot, mindig külső iránymutatásra vár a legegyszerűbb feladatoknál is."
    ]
    
    neutral_texts = [
        "Általában megbízható, de időnként előfordulnak apróbb hibák a munkájában. Összességében jó vele együtt dolgozni.",
        "A kötelező feladatokat elvégzi, de ritkán mutat proaktivitást vagy hoz új ötleteket a csapatba.",
        "Alapvetően rendben van a teljesítménye, de a stresszesebb időszakokban hajlamos a kapkodásra.",
        "Megfelelően végzi a munkáját, bár a kommunikációja lehetne egy kicsit nyitottabb és proaktívabb.",
        "Stabil közepes teljesítményt nyújt. Vannak jobb és rosszabb napjai, de alapvetően beilleszkedik a csapatba."
    ]

    for i in range(n):
        target_name = get_emp_name(i)
        
        evaluator1 = get_emp_name(i + 1)
        evaluator2 = get_emp_name(i + 2) if n > 2 else get_emp_name(i)
        evaluator3 = get_emp_name(i + 3) if n > 3 else get_emp_name(i + 1)

        # 1. Good Review
        send_form.append({
            "form_filler": evaluator1,
            "target": target_name,
            "form_type": "Leader",
            "form_id": form_id
        })
        ans_good = {}
        for q in form1_qs:
            q_id, _, q_type = q[0], q[1], q[3]
            if q_type == "0-5 Rating":
                ans_good[q_id] = random.randint(4, 5)
            elif q_type == "Text Box":
                ans_good[q_id] = good_texts[(q_id + i) % len(good_texts)]
        responses_to_submit.append((form1_obj, ans_good, evaluator1))

        # 2. Bad Review
        send_form.append({
            "form_filler": evaluator2,
            "target": target_name,
            "form_type": "Peer",
            "form_id": form2_id
        })
        ans_bad = {}
        for q in form2_qs:
            q_id, _, q_type = q[0], q[1], q[3]
            if q_type == "0-5 Rating":
                ans_bad[q_id] = random.randint(1, 2)
            elif q_type == "Text Box":
                ans_bad[q_id] = bad_texts[(q_id + i) % len(bad_texts)]
        responses_to_submit.append((form2_obj, ans_bad, evaluator2))

        # 3. Neutral Review (Only if enough employees)
        if n > 3:
            send_form.append({
                "form_filler": evaluator3,
                "target": target_name,
                "form_type": "Peer",
                "form_id": form2_id
            })
            ans_neutral = {}
            for q in form2_qs:
                q_id, _, q_type = q[0], q[1], q[3]
                if q_type == "0-5 Rating":
                    ans_neutral[q_id] = random.randint(3, 4)
                elif q_type == "Text Box":
                    ans_neutral[q_id] = neutral_texts[(q_id + i) % len(neutral_texts)]
            responses_to_submit.append((form2_obj, ans_neutral, evaluator3))

    add_form_assignments(send_form)
    
    for f_obj, ans, f_name in responses_to_submit:
        f_obj.submit_response(ans, f_name)

    for f_id in [form_id, form2_id]:
        assigns = get_assignments_by_form(f_id)
        if assigns:
            for assign in assigns:
                update_assignment_status(assign[0], 'completed')
