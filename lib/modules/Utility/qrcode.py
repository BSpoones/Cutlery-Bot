"""
/qrcode command
Developed by Bspoones - Oct 2022
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#QRCode
"""

import tanjun, qrcode, hikari
from tanjun.abc import Context as Context
from io import BytesIO
from PIL import Image

from lib.core.client import Client
from lib.utils.command_utils import auto_embed, log_command
from . import COG_TYPE, COG_LINK

LOGO_LINK = r'./assets/logos/qrcode_logo.png'


qrcode_component = tanjun.Component()

@qrcode_component.add_slash_command
@tanjun.with_bool_slash_option("removelogo","Remove the BSpoones logo from the QR code?", default=False)
@tanjun.with_str_slash_option("url","URL to convert to a QR code")
@tanjun.as_slash_command("qrcode","Generates a QR code")
async def qrcode_command(ctx: Context, url: str, removelogo: bool):
    # Opening logo    
    logo = Image.open(LOGO_LINK)
    
    # Width in pixels for the logo
    basewidth = 100
    # Resizing the logo to the basewidth
    wpercent = (basewidth/float(logo.size[0]))
    hsize = int((float(logo.size[1])*float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
    QRcode = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
        
    # Adding url data to the QRcode
    QRcode.add_data(url)
    
    # generating QR code
    QRcode.make()
    
    # Setting FG colour
    QRcolor = 'Black'
    
    # Setting BG colour
    QRimg = QRcode.make_image(fill_color=QRcolor, back_color="white").convert('RGB')
    
    # Adding logo to the QR code
    if not removelogo:
        pos = (
            (QRimg.size[0] - logo.size[0]) // 2, # X
            (QRimg.size[1] - logo.size[1]) // 2  # Y
            )
        QRimg.paste(logo, pos)
    
    # Converting the image to a byters object
    with BytesIO() as image_binary:
        QRimg.save(image_binary, 'PNG')
        image_binary.seek(0)
        file= hikari.Bytes(image_binary,'image.png')
        
    embed = auto_embed(
            type="info",
            author=COG_TYPE,
            author_url = COG_LINK,
            title=f"QR code generated",
            image = file,
            ctx=ctx
        )
    await ctx.respond(embed=embed)
    log_command(ctx,"qrcode",url)

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(qrcode_component.copy())