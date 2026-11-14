from dataclasses import dataclass, field
from drafter import *

# --------------------------------------------------
# WATTWISE: ELECTRICITY BILL CALCULATOR
# --------------------------------------------------

# Sample electricity rates in dollars per kWh.
# Add the remaining states from your original dictionary here.
electricity_rates = {
    "Delaware": 0.1929,
    "Maryland": 0.1900,
    "Virginia": 0.1400,
    "Pennsylvania": 0.1800,
    "District of Columbia": 0.2200
}

set_website_title("Electricity Bill Calculator")
set_site_information(
    author="Chris Stewart",
    description="Calculate your electricity bill.",
    sources="My dad, My friend Jire, ChatGPT.",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/your-username/your-repository"]
)
hide_debug_information()
set_website_framed(False)
# --------------------------------------------------
# DATA MODELS
# --------------------------------------------------

@dataclass
class Appliance:
    """Store information about one household appliance."""
    name: str
    power_watts: float
    hours_per_day: float
    kwh_per_month: float


@dataclass
class State:
    """Store the user's calculator data and bill history."""
    location: str = "Delaware"
    rate: float = 0.1929
    usage: float = 0.0
    bill: float = 0.0
    solar_offset: float = 0.0
    notes: str = ""
    appliances: list = field(default_factory=list)
    history: list = field(default_factory=list)


# --------------------------------------------------
# ELECTRICAL CALCULATIONS
# --------------------------------------------------

def watt_per_day(power_watts: float, hours_per_day: float) -> float:
    """Calculate an appliance's daily energy use in watt-hours."""
    return power_watts * hours_per_day


def monthly_kwh(power_watts: float, hours_per_day: float) -> float:
    """Estimate monthly energy consumption in kilowatt-hours."""
    daily_wh = watt_per_day(power_watts, hours_per_day)
    return daily_wh * 30 / 1000


def calculate_cost(usage_kwh: float, rate: float) -> float:
    """Calculate electricity cost before solar offsets."""
    return usage_kwh * rate


def net_usage(usage_kwh: float, solar_offset: float) -> float:
    """Estimate grid energy needed after a solar energy offset."""
    return max(0, usage_kwh - solar_offset)


def total_appliance_usage(appliances: list) -> float:
    """Add the monthly energy use of all saved appliances."""
    total = 0.0

    for appliance in appliances:
        total += appliance.kwh_per_month

    return total


# --------------------------------------------------
# PAGE 1: HOME
# --------------------------------------------------

@route
def index(state: State) -> Page:
    """Display the WattWise home page and navigation."""
    return Page(state, [
        Header("⚡ WATTWISE"),
        Text("HOUSEHOLD ENERGY DASHBOARD"),
        Text("Understand your electricity. Control your costs."),
        
     
        Text("\nEstimate your monthly electricity bill using "
             "appliance wattage and daily usage."),
        Button("Open Bill Calculator", "calculator"),
        Button("My Appliances", "appliances"),
        Button("Bill History", "history"),
        Button("About WattWise", "about")
    ])


# --------------------------------------------------
# PAGE 2: BILL CALCULATOR
# --------------------------------------------------

@route
def calculator(state: State) -> Page:
    """Display the electricity calculator form."""
    return Page(state, [
        Header("⚡ Electricity Calculator"),
        Text("Enter your appliance and energy details."),
        Text("LOCATION"),
        SelectBox("location", list(electricity_rates.keys())),
        Text("APPLIANCE"),
        TextBox("appliance_name", "Air conditioner"),
        Text("POWER RATING (WATTS)"),
        TextBox("power_watts", 1500, kind="number"),
        Text("HOURS USED PER DAY"),
        TextBox("hours_per_day", 8, kind="number"),
        Text("SOLAR OFFSET (kWh/month)"),
        TextBox("solar_offset", 0, kind="number"),
        Text("NOTES (OPTIONAL)"),
        TextArea("notes"),
        Button("⚡ Calculate My Bill", "calculate_bill"),
        Button("Back to Home", "index")
    ])


# --------------------------------------------------
# PAGE 3: CALCULATION RESULTS
# --------------------------------------------------

@route
def calculate_bill(
    state: State,
    location: str,
    appliance_name: str,
    power_watts: float,
    hours_per_day: float,
    solar_offset: float,
    notes: str = ""
) -> Page:
    """Calculate a bill estimate and display the results."""

    # Select the electricity rate for the chosen location.
    if location in electricity_rates:
        state.location = location
        state.rate = electricity_rates[location]
    else:
        state.location = "Delaware"
        state.rate = electricity_rates["Delaware"]

    # Validate the numeric inputs.
    if power_watts < 0 or hours_per_day < 0 or solar_offset < 0:
        return Page(state, [
            Header("Input Error"),
            Text("Power, hours, and solar offset cannot be negative."),
            Button("Try Again", "calculator")
        ])

    if hours_per_day > 24:
        return Page(state, [
            Header("Input Error"),
            Text("Hours used per day must be 24 or less."),
            Button("Try Again", "calculator")
        ])

    # Calculate energy consumption and cost.
    usage = monthly_kwh(power_watts, hours_per_day)
    grid_usage = net_usage(usage, solar_offset)
    bill = calculate_cost(grid_usage, state.rate)

    state.usage = usage
    state.solar_offset = solar_offset
    state.bill = bill
    state.notes = notes

    # Save the appliance.
    appliance = Appliance(
        appliance_name,
        power_watts,
        hours_per_day,
        usage
    )
    state.appliances.append(appliance)

    # Save this calculation in the session history.
    state.history.append(
        f"{location}: {appliance_name} — "
        f"{usage:.2f} kWh/month, estimated cost ${bill:.2f}"
    )

    return Page(state, [
        Header("⚡ Your Energy Report"),
        
        Text("LOCATION: " + state.location),
        Text("ELECTRICITY RATE: $" + f"{state.rate:.4f}" + "/kWh"),
        Text("APPLIANCE: " + appliance_name),
        Text("POWER: " + f"{power_watts:.0f}" + " W"),
        Text("DAILY USE: " + f"{hours_per_day:.2f}" + " hours"),
        Text("MONTHLY ENERGY: " + f"{usage:.2f}" + " kWh"),
        Text("SOLAR OFFSET: " + f"{solar_offset:.2f}" + " kWh"),
        Text("ESTIMATED GRID ENERGY: " + f"{grid_usage:.2f}" + " kWh"),
       
        Text("ESTIMATED COST: $" + f"{bill:.2f}" + " per month"),
        Text("Note: This estimate excludes fixed fees, taxes, "
             "and other utility charges."),
        Button("Calculate Another Appliance", "calculator"),
        Button("View My Appliances", "appliances"),
        Button("Home", "index")
    ])


# --------------------------------------------------
# PAGE 4: APPLIANCE LIST
# --------------------------------------------------

@route
def appliances(state: State) -> Page:
    """Display appliances saved during this session."""
    content = [
        Header("⚡ My Appliances"),
        Text("Your saved household electrical loads.")
    ]

    # Display each appliance in the saved list.
    if len(state.appliances) == 0:
        content.append(Text("No appliances saved yet."))
    else:
        for appliance in state.appliances:
            content.append(
                Text(
                    appliance.name + " | "
                    + f"{appliance.power_watts:.0f} W | "
                    + f"{appliance.hours_per_day:.1f} hours/day | "
                    + f"{appliance.kwh_per_month:.2f} kWh/month"
                )
            )

        total_usage = total_appliance_usage(state.appliances)
        
        content.append(Text("TOTAL MONTHLY ENERGY: "
                            + f"{total_usage:.2f}" + " kWh"))

    content.append(Button("Add an Appliance", "add_appliance"))
    content.append(Button("Calculate a Bill", "calculator"))
    content.append(Button("Home", "index"))

    return Page(state, content)


# --------------------------------------------------
# PAGE 5: ADD AN APPLIANCE
# --------------------------------------------------

@route
def add_appliance(state: State) -> Page:
    """Display a form for adding an appliance."""
    return Page(state, [
        Header("＋ Add an Appliance"),
        Text("Enter the appliance's electrical specifications."),
        Text("APPLIANCE NAME"),
        TextBox("appliance_name", "LED lighting"),
        Text("POWER RATING (WATTS)"),
        TextBox("power_watts", 10, kind="number"),
        Text("HOURS USED PER DAY"),
        TextBox("hours_per_day", 5, kind="number"),
        Button("Save Appliance", "save_appliance"),
        Button("Back to Appliances", "appliances")
    ])


@route
def save_appliance(
    state: State,
    appliance_name: str,
    power_watts: float,
    hours_per_day: float
) -> Page:
    """Validate and save a new appliance."""
    if power_watts < 0 or hours_per_day < 0:
        return Page(state, [
            Header("Input Error"),
            Text("Power and hours cannot be negative."),
            Button("Try Again", "add_appliance")
        ])

    if hours_per_day > 24:
        return Page(state, [
            Header("Input Error"),
            Text("Hours used per day must be 24 or less."),
            Button("Try Again", "add_appliance")
        ])

    usage = monthly_kwh(power_watts, hours_per_day)

    state.appliances.append(
        Appliance(
            appliance_name,
            power_watts,
            hours_per_day,
            usage
        )
    )

    return Page(state, [
        Header("✓ Appliance Saved"),
        Text(appliance_name + " has been added."),
        Text("Estimated monthly energy: " + f"{usage:.2f}" + " kWh"),
        Button("View Appliances", "appliances"),
        Button("Add Another", "add_appliance"),
        Button("Home", "index")
    ])


# --------------------------------------------------
# PAGE 6: BILL HISTORY
# --------------------------------------------------

@route
def history(state: State) -> Page:
    """Display previous bill calculations from this session."""
    content = [
        Header("▤ Bill History"),
        Text("Your previous calculations in this session.")
    ]

    if len(state.history) == 0:
        content.append(Text("No calculations recorded yet."))
    else:
        for entry in state.history:
            content.append(Text("• " + entry))

    content.append(Button("Calculate a New Bill", "calculator"))
    content.append(Button("Home", "index"))

    return Page(state, content)


# --------------------------------------------------
# PAGE 7: ABOUT
# --------------------------------------------------

@route
def about(state: State) -> Page:
    """Explain the purpose and calculation method of WattWise."""
    return Page(state, [
        Header("About WattWise"),
        Text("\n" + "WattWise is a household electricity estimator."),
        Text("\n" + "HOW THE ELECTRICAL CALCULATION WORKS"),
        Text("Energy (Wh) = Power (W) × Time (hours)"),
        Text("Energy (kWh) = Energy (Wh) ÷ 1000"),
        Text("Monthly energy = Daily energy × 30"),
        Text("Estimated cost = Grid energy (kWh) × Rate ($/kWh)"),
        Text("A solar offset is subtracted from estimated monthly "
             "energy use, with grid usage limited to zero or above."),
        Text("This is a simplified estimate, not a utility bill."),
        Button("Open Calculator", "calculator"),
        Button("Home", "index")
    ])


# --------------------------------------------------
# UNIT TESTS
# --------------------------------------------------
# These direct assertions assume assert_equal is supplied
# by your course environment.

assert_equal(watt_per_day(100, 5), 500)
assert_equal(monthly_kwh(100, 5), 15)
assert_equal(calculate_cost(100, 0.20), 20)
assert_equal(net_usage(100, 25), 75)
assert_equal(net_usage(100, 150), 0)
assert_equal(total_appliance_usage([
    Appliance("Lamp", 10, 5, 1.5),
    Appliance("Fan", 50, 4, 6.0)
]), 7.5)


# --------------------------------------------------
# START THE WEBSITE
# --------------------------------------------------

start_server(State())
