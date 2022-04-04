import hikari
from hikari.messages import ButtonStyle



DELETE_CUSTOM_ID = "AUTHOR_DELETE_BUTTON"

EMPTY_ROW = (
    hikari.impl.ActionRowBuilder()
    .add_button(ButtonStyle.SECONDARY,"Expired")
    .set_label("Buttons expired, run command again to view")
    .set_is_disabled(True)
    .add_to_container()
)
ONE_PAGE_ROW = (
    hikari.impl.ActionRowBuilder()
    .add_button(ButtonStyle.SECONDARY,"Expired")
    .set_label("There is only one page")
    .set_is_disabled(True)
    .add_to_container()
)

DELETE_ROW = (
    hikari.impl.ActionRowBuilder()
    .add_button(hikari.ButtonStyle.DANGER, DELETE_CUSTOM_ID)
    .set_emoji("❌")
    .add_to_container()
)

PAGENATE_ROW = (
    hikari.impl.ActionRowBuilder()
    .add_button(ButtonStyle.PRIMARY, "FIRST")
    .set_emoji("⏮")
    .add_to_container()
    
    .add_button(ButtonStyle.PRIMARY, "BACK")
    .set_emoji("◀")
    .add_to_container()

    .add_button(ButtonStyle.PRIMARY, "NEXT")
    .set_emoji("▶")
    .add_to_container()
    
    .add_button(ButtonStyle.PRIMARY, "LAST")
    .set_emoji("⏭")
    .add_to_container()
    
    .add_button(ButtonStyle.DANGER, DELETE_CUSTOM_ID)
    .set_emoji("❌")
    .add_to_container()

)

TIMELINE_ROW = (
    hikari.impl.ActionRowBuilder()  
    .add_button(ButtonStyle.PRIMARY, "BACK")
    .set_emoji("◀")
    .add_to_container()

    .add_button(ButtonStyle.PRIMARY, "NEXT")
    .set_emoji("▶")
    .add_to_container()
    
    .add_button(ButtonStyle.DANGER, DELETE_CUSTOM_ID)
    .set_emoji("❌")
    .add_to_container()

)

UNDO_ROW = (
    hikari.impl.ActionRowBuilder()
    .add_button(ButtonStyle.PRIMARY, "UNDO")
    .set_emoji("↩")
    .set_label("Undo command")
    .add_to_container()
    
    .add_button(ButtonStyle.DANGER, DELETE_CUSTOM_ID)
    .set_emoji("❌")
    .add_to_container()
)