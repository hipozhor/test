from aiogram.fsm.state import State, StatesGroup

class SearchCityStates(StatesGroup):
    waiting_for_query = State()
    choosing_location = State()