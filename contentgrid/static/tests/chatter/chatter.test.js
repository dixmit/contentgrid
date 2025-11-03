import {
    click,
    contains,
    openFormView,
    start,
    startServer,
} from "@mail/../tests/mail_test_helpers";
import {expect, test} from "@odoo/hoot";
import {animationFrame} from "@odoo/hoot-dom";
import {defineContentgridModels} from "@contentgrid/../tests/contentgrid_test_helpers.esm";

defineContentgridModels();

test("simple chatter on a record. No ContentGrid", async () => {
    const pyEnv = await startServer();
    await start();
    const partnerId = pyEnv["res.partner"].create({name: "John Doe"});
    pyEnv["ir.attachment"].create({
        name: "Initial Attachment",
        res_model: "res.partner",
        res_id: partnerId,
        datas: "SGVsbG8sIFdvcmxkIQ==",
    });
    await openFormView("res.partner", partnerId);
    await contains(".o-mail-Chatter-attachFiles sup", {text: "1"});
    expect(".o-mail-Chatter-showContentGrid").toHaveCount(0);
    click(".o-mail-Chatter-attachFiles");
    await animationFrame();
    expect(".o-mail-AttachmentCard").toHaveCount(1);
});
test("simple chatter on a record. ContentGrid Button. One record related", async () => {
    const pyEnv = await startServer();
    await start();
    const partnerId = pyEnv["res.partner"].create({name: "John Doe"});
    pyEnv["contentgrid.record"].create({
        contentgrid_connection_id: 1,
        res_model: "res.partner",
        res_id: partnerId,
        name: "CG Record Code",
        element: "partner",
        data: '{ "foo": "bar" }',
    });
    const attachmentId = pyEnv["ir.attachment"].create({
        name: "Initial Attachment",
        res_model: "res.partner",
        res_id: partnerId,
        datas: "SGVsbG8sIFdvcmxkIQ==",
    });

    pyEnv["contentgrid.record"].create({
        contentgrid_connection_id: 1,
        res_model: "ir.attachment",
        res_id: attachmentId,
        name: "CG Attachment Code",
        element: "attachment",
    });
    await openFormView("res.partner", partnerId);
    await contains(".o-mail-Chatter-attachFiles sup", {text: "1"});
    expect(".o-mail-Chatter-showContentGrid").toHaveCount(1);
    expect(".o-ContentGridDialog-openInContentGrid").toHaveCount(0);
    await click(".o-mail-Chatter-showContentGrid");
    await animationFrame();
    expect(".o-ContentGridDialog-openInContentGrid").toHaveCount(1);
    expect(".o-ContentGridDialog-recordSelector").toHaveCount(0);
});
test("simple chatter on a record. ContentGrid Button. Two records related", async () => {
    const pyEnv = await startServer();
    await start();
    const partnerId = pyEnv["res.partner"].create({name: "John Doe"});
    pyEnv["contentgrid.record"].create({
        contentgrid_connection_id: 1,
        res_model: "res.partner",
        res_id: partnerId,
        name: "CG Record Code",
        element: "partner",
        data: '{ "foo": "bar" }',
    });
    pyEnv["contentgrid.record"].create({
        contentgrid_connection_id: 1,
        res_model: "res.partner",
        res_id: partnerId,
        name: "CG Record Code2",
        element: "partner2",
        data: '{ "foo": "bar" }',
    });
    const attachmentId = pyEnv["ir.attachment"].create({
        name: "Initial Attachment",
        res_model: "res.partner",
        res_id: partnerId,
        datas: "SGVsbG8sIFdvcmxkIQ==",
    });

    pyEnv["contentgrid.record"].create({
        contentgrid_connection_id: 1,
        res_model: "ir.attachment",
        res_id: attachmentId,
        name: "CG Attachment Code",
        element: "attachment",
    });
    await openFormView("res.partner", partnerId);
    await contains(".o-mail-Chatter-attachFiles sup", {text: "1"});
    expect(".o-mail-Chatter-showContentGrid").toHaveCount(1);
    await click(".o-mail-Chatter-showContentGrid");
    await animationFrame();
    expect(".o-ContentGridDialog-openInContentGrid").toHaveCount(1);
    expect(".o-ContentGridDialog-recordSelector").toHaveCount(2);
});
test("simple chatter on a record. ContentGrid Attachments", async () => {
    const pyEnv = await startServer();
    await start();
    const partnerId = pyEnv["res.partner"].create({name: "John Doe"});
    pyEnv["contentgrid.record"].create({
        contentgrid_connection_id: 1,
        res_model: "res.partner",
        res_id: partnerId,
        name: "CG Record Code",
        element: "partner",
        data: '{ "foo": "bar" }',
    });
    const attachmentId = pyEnv["ir.attachment"].create({
        name: "Initial Attachment",
        res_model: "res.partner",
        res_id: partnerId,
        datas: "SGVsbG8sIFdvcmxkIQ==",
    });

    pyEnv["contentgrid.record"].create({
        contentgrid_connection_id: 1,
        res_model: "ir.attachment",
        res_id: attachmentId,
        name: "CG Attachment Code",
        element: "attachment",
        data: '{ "foo": "bar" }',
    });
    await openFormView("res.partner", partnerId);
    await contains(".o-mail-Chatter-attachFiles sup", {text: "1"});
    click(".o-mail-Chatter-attachFiles");
    await animationFrame();
    expect(".o-AttachmentCard-openInContentGrid").toHaveCount(1);
    click(".o-AttachmentCard-openInContentGrid");
    await animationFrame();
    expect(".o-ContentGridDialog-openInContentGrid").toHaveCount(1);
});
