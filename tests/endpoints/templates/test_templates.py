from http import HTTPStatus

from endpoints.templates.requests import (
    create_template,
    delete_template,
    get_template,
    get_templates,
    render_template,
    update_template,
)

from internal.templates import wrapping


async def test_create_template(app_fixture):
    response, data = await create_template(app_fixture)

    assert response.status_code == HTTPStatus.CREATED, data
    assert data["id"], data


async def test_template_create_base(app_fixture):
    response, data = await create_template(
        app_fixture, is_base=True, content="Pepa\n" + wrapping.content_block("")
    )

    assert data["slug"] == wrapping.BASE_TEMPLATE_NAME


async def test_get_templates(app_fixture):
    await create_template(app_fixture)

    response, data = await get_templates(app_fixture)

    assert response.status_code == HTTPStatus.OK, data
    assert len(data["data"]) != 0


async def test_get_template(app_fixture):
    _, template = await create_template(app_fixture)

    response, data = await get_template(app_fixture, template["id"])

    assert response.status_code == HTTPStatus.OK, data
    assert data["id"] == template["id"]


async def test_update_template(app_fixture):
    _, template = await create_template(app_fixture)
    template["name"] = "new_template_name"

    response, data = await update_template(app_fixture, template["id"], template)

    assert response.status_code == HTTPStatus.OK, data
    assert data["name"] == template["name"], data


async def test_delete_template(app_fixture):
    _, template = await create_template(app_fixture)

    response, data = await delete_template(app_fixture, template["id"])

    find_response, _ = await get_template(app_fixture, template["id"])
    assert response.status_code == HTTPStatus.OK, data
    assert find_response.status_code == HTTPStatus.NOT_FOUND


async def test_template_render_failed_no_base_template(app_fixture):
    _, template = await create_template(app_fixture)

    response, data = await render_template(app_fixture, template["id"])

    assert response.status_code == HTTPStatus.BAD_REQUEST, data


async def test_template_create_base_failed_no_content_block(app_fixture):
    response, data = await create_template(app_fixture, is_base=True)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, data


async def test_template_render(app_fixture):
    checking_word = "PepeTronnio"
    _, base_template = await create_template(
        app_fixture,
        is_base=True,
        content=f"{checking_word}\n" + wrapping.content_block(""),
    )
    _, created_templ = await create_template(app_fixture, content="Notification!")

    response, data = await render_template(app_fixture, created_templ["id"])

    assert checking_word in response.text
