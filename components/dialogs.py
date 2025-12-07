"""
Reusable components for JUDGEMENOT app
Place this file in: components/common_components.py
"""

import flet as ft


def create_header(page: ft.Page):
    """Create the standard header with logo and About/Contact buttons"""
    
    # Circular rounded hammer logo
    logo = ft.Container(
        width=45,
        height=45,
        border_radius=50,
        bgcolor="transparent",
        border=ft.border.all(2, ft.Colors.BLACK),
        padding=5,
        content=ft.Image(
            src="hammer.png",
            fit=ft.ImageFit.CONTAIN
        )
    )

    header_left = ft.Row(
        spacing=10,
        controls=[
            logo,
            ft.Text("JUDGEMENOT", size=22, weight="bold", color=ft.Colors.BLACK),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    header_right = ft.Row(
        spacing=40,
        controls=[
            ft.TextButton(
                "ABOUT", 
                style=ft.ButtonStyle(color=ft.Colors.BLACK), 
                on_click=lambda e: show_about_dialog(page)
            ),
            ft.TextButton(
                "CONTACT", 
                style=ft.ButtonStyle(color=ft.Colors.BLACK), 
                on_click=lambda e: show_contact_dialog(page)
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    header = ft.Container(
        height=75,
        padding=ft.padding.symmetric(horizontal=50),
        bgcolor="#80C1FF",
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[header_left, header_right],
        )
    )
    
    return header


def show_about_dialog(page: ft.Page):
    """Display the About JUDGEMENOT dialog"""
    
    def create_member_card(name, position, section, image_path="placeholder.jpg"):
        return ft.Container(
            width=200,
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    # Placeholder image frame
                    ft.Container(
                        width=120,
                        height=120,
                        border_radius=60,
                        bgcolor=ft.Colors.GREY_200,
                        border=ft.border.all(2, ft.Colors.BLUE_300),
                        content=ft.Image(
                            src=image_path,
                            width=120,
                            height=120,
                            fit=ft.ImageFit.COVER,
                            border_radius=60,
                        )
                    ),
                    ft.Text(name, size=16, weight="bold", color=ft.Colors.BLACK),
                    ft.Text(position, size=13, color=ft.Colors.BLUE_700, italic=True),
                    ft.Text(section, size=12, color=ft.Colors.GREY_700),
                ]
            )
        )
    
    def close_dialog(dialog):
        dialog.open = False
        page.update()
    
    about_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("About JUDGEMENOT", size=24, weight="bold"),
        content=ft.Container(
            width=700,
            content=ft.Column(
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    # Team Members Section
                    ft.Container(
                        content=ft.Text("Our Team", size=18, weight="bold", color=ft.Colors.BLACK),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20,
                            controls=[
                                create_member_card(
                                    "Elmskie", 
                                    "Project Lead", 
                                    "BSCS 3A",
                                    "doge1.jpg"
                                ),
                                create_member_card(
                                    "Sijay", 
                                    "Developer", 
                                    "BSCS 3A",
                                    "doge2.jpg"
                                ),
                                create_member_card(
                                    "Rv", 
                                    "Designer", 
                                    "BSCS 3A",
                                    "doge3.jpg"
                                ),
                            ]
                        ),
                    ),
                    
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    
                    # Project Description Section
                    ft.Container(
                        content=ft.Text("Our Mission", size=18, weight="bold", color=ft.Colors.BLACK),
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(
                        "Judgemenot is a tabulation system designed to promote transparency and fairness. "
                        "It allows users to view scores and results in real time, ensuring that all participants can track updates instantly. "
                        "Our platform is intuitive and user-friendly, providing a clear and accurate visualization of scores while maintaining integrity and reliability.",
                        size=14,
                        color=ft.Colors.BLACK87,
                    ),
                ]
            )
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda e: close_dialog(about_dialog))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.overlay.append(about_dialog)
    about_dialog.open = True
    page.update()


def show_contact_dialog(page: ft.Page):
    """Display the Contact Us dialog"""
    
    def create_contact_item(icon, title, value, color=ft.Colors.BLUE_700):
        return ft.Container(
            padding=15,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
            content=ft.Row(
                spacing=15,
                controls=[
                    ft.Icon(icon, color=color, size=28),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(title, size=12, color=ft.Colors.GREY_700, weight="bold"),
                            ft.Text(value, size=14, color=ft.Colors.BLACK, selectable=True),
                        ]
                    )
                ]
            )
        )
    
    def close_dialog(dialog):
        dialog.open = False
        page.update()
    
    contact_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Contact Us", size=24, weight="bold"),
        content=ft.Container(
            width=500,
            content=ft.Column(
                spacing=15,
                controls=[
                    ft.Text(
                        "Get in touch with the JUDGEMENOT team. We're here to help!",
                        size=14,
                        color=ft.Colors.GREY_700,
                    ),
                    
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    
                    # Contact Information
                    create_contact_item(
                        ft.Icons.EMAIL,
                        "Email",
                        "judgemenot.team@cspc.edu.ph",
                        ft.Colors.BLUE_700
                    ),
                    
                    create_contact_item(
                        ft.Icons.PHONE,
                        "Phone",
                        "+63 123 456 7890",
                        ft.Colors.GREEN_700
                    ),
                    
                    create_contact_item(
                        ft.Icons.LOCATION_ON,
                        "Office Address",
                        "CSPC Campus, Nabua, Camarines Sur",
                        ft.Colors.RED_700
                    ),
                    
                    create_contact_item(
                        ft.Icons.SCHEDULE,
                        "Office Hours",
                        "Monday - Friday, 8:00 AM - 5:00 PM",
                        ft.Colors.ORANGE_700
                    ),
                    
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    
                    ft.Text(
                        "For technical support or inquiries about the system, please don't hesitate to reach out.",
                        size=12,
                        color=ft.Colors.GREY_600,
                        italic=True,
                    ),
                ]
            )
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda e: close_dialog(contact_dialog))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.overlay.append(contact_dialog)
    contact_dialog.open = True
    page.update()