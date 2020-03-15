import datetime

import streamlit as st

import graphing
import models
from data import constants
from fetch_live_data import DATESTRING_FORMAT, LOG_PATH
from utils import generate_html, COLOR_MAP

# estimates from https://github.com/midas-network/COVID-19/tree/master/parameter_estimates/2019_novel_coronavirus

DATESTRING_FORMAT_READABLE = "%A %d %B %Y" # 'Sunday 30 November 2014'

class Sidebar:
    country = st.sidebar.selectbox(
        "What country do you live in?", options=constants.Countries.countries
    )

    if country:
        transmission_probability = constants.TransmissionRatePerContact.default
        country_data = constants.Countries.country_data[country]
        with open(LOG_PATH) as f:
            date_last_fetched = f.read()
            date_last_fetched = datetime.datetime.strptime(
                date_last_fetched, DATESTRING_FORMAT
            ).strftime(DATESTRING_FORMAT_READABLE)

        st.sidebar.markdown(
            body=generate_html(text=f"Current date and stats", line_height=0, font_family="Arial",),
            unsafe_allow_html=True
        )

        st.sidebar.markdown(
            body=generate_html(text=f"{date_last_fetched}", bold=True, color=COLOR_MAP["pink"], line_height=0,),
            unsafe_allow_html=True
        )

        st.sidebar.markdown(
            body=generate_html( 
                text=f'Population: {int(country_data["Population"]):,}<br>Infected: {country_data["Confirmed"]}<br>Recovered: {country_data["Recovered"]}<br>Dead: {country_data["Deaths"]}',
                line_height=0,
                font_family="Arial",
                font_size="0.9rem",
                tag="p",
            ),
            unsafe_allow_html=True
        )
        # Horizontal divider line
        st.sidebar.markdown("-------")

    contact_rate = st.sidebar.slider(
        label="Number of people infected people come into contact with daily",
        min_value=constants.AverageDailyContacts.min,
        max_value=constants.AverageDailyContacts.max,
        value=constants.AverageDailyContacts.default,
    )

    horizon = {'3  months': 90,
               '6 months': 180,
               '12  months': 365}
    _num_days_for_prediction = st.sidebar.radio(label="What period of time would you like to predict for?",
                                                options=list(horizon.keys()),
                                                index=0)

    num_days_for_prediction = horizon[_num_days_for_prediction]


def run_app():
    st.markdown(
        body=generate_html( 
            text=f'Corona Calculator',
            bold=True,
            tag="h2",
        ),
        unsafe_allow_html=True
    )
    st.markdown(
        body=generate_html( 
            text=f'The goal of this data viz is to help you visualize what is the impact of having infected people entering in contact with other people<hr>',
            tag="h4",
        ),
        unsafe_allow_html=True
    )

    Sidebar()
    country = Sidebar.country
    number_cases_confirmed = constants.Countries.country_data[country]["Confirmed"]
    population = constants.Countries.country_data[country]["Population"]
    num_hospital_beds = constants.Countries.country_data[country]["Num Hospital Beds"]

    # We don't have this for now
    # num_ventilators = constants.Countries.country_data[country]["Num Ventilators"]

    sir_model = models.SIRModel(
        constants.TransmissionRatePerContact.default,
        Sidebar.contact_rate,
        constants.RemovalRate.default,
    )
    true_cases_estimator = models.TrueInfectedCasesModel(
        constants.AscertainmentRate.default
    )
    death_toll_model = models.DeathTollModel(constants.MortalityRate.default)
    hospitalization_model = models.HospitalizationModel(
        constants.HospitalizationRate.default, constants.VentilationRate.default
    )

    df = models.get_predictions(
        true_cases_estimator,
        sir_model,
        death_toll_model,
        hospitalization_model,
        number_cases_confirmed,
        population,
        Sidebar.num_days_for_prediction,
    )

    st.write("The number of reported cases radically underestimates the true cases. The extent depends upon "
             "your country's testing strategy. Using numbers from Japan, we estimate the true number of cases "
             "looks something like:")

    fig = graphing.plot_true_versus_confirmed(number_cases_confirmed, true_cases_estimator.predict(number_cases_confirmed))
    st.write(fig)
    st.write(
        "The critical factor for controlling spread is how many others infected people interact with each day. "
        "This has a dramatic effect upon the dynamics of the disease. "
    )
    st.write('**Play with the slider to the left to see how this changes the dynamics of disease spread**')

    df_base = df[~df.Status.isin(["Need Hospitalization", "Need Ventilation"])]
    base_graph = graphing.infection_graph(df_base)
    st.write(base_graph)

    # TODO: psteeves can you confirm total number of deaths should change? Not clear to me why this would be
    # apart from herd immunity?
    # st.write('Note how the speed of spread affects both the *peak number of cases* and the *total number of deaths*.')

    hospital_graph = graphing.hospitalization_graph(
        df[df.Status.isin(["Infected", "Need Hospitalization"])],
        num_hospital_beds,
        None
    )

    st.title("How will this affect my healthcare system?")
    st.write(
        "The important variable for hospitals is the peak number of people who require hospitalization"
        " and ventilation at any one time."
    )

    # Do some rounding to avoid beds sounding too precise!
    st.write(f'Your country has around **{round(num_hospital_beds / 100) * 100:,}** beds. Bear in mind that most of these '
             'are probably already in use for people sick for other reasons.')
    st.write("It's hard to know how many ventilators are present per country, but there will certainly be a worldwide"
             "shortage. Many countries are scrambling to buy them [(source)](https://www.reuters.com/article/us-health-coronavirus-draegerwerk-ventil/germany-italy-rush-to-buy-life-saving-ventilators-as-manufacturers-warn-of-shortages-idUSKBN210362).")

    st.write(hospital_graph)
    peak_occupancy = df.loc[df.Status == "Need Hospitalization"]["Forecast"].max()
    percent_beds_at_peak = min(100 * num_hospital_beds / peak_occupancy, 100)

    # peak_ventilation = df.loc[df.Status == "Ventilated"]["Forecast"].max()
    # percent_ventilators_at_peak = min(
    #     100 * Sidebar.number_of_ventilators / peak_ventilation, 100
    # )

    st.markdown(
        f"At peak, **{peak_occupancy:,}** people will need hospital beds. ** {percent_beds_at_peak:.1f} % ** of people "
        f"who need a bed in hospital will have access to one given your country's historical resources. This does "
        f"not take into account any special measures that may have been taken in the last few months."
    )
    # st.markdown(
    #     f"At peak, ** {percent_ventilators_at_peak:.1f} % ** of people who need a ventilator have one"
    # )


if __name__ == "__main__":
    run_app()
