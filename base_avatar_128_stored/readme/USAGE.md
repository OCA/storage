When using `fs_attachment` with a slow backend, the partners kanban view can be
slow. This is because of an Odoo
[bug](https://github.com/odoo/odoo/pull/221270#issuecomment-3511712521) which
causes it to unnecessarily read image content from the file store when it only
needs the size.

The [patch](https://github.com/odoo/odoo/pull/221270) that was applied in Odoo
17+ in summer 2025 helps in some circumstances such as the products kanban view,
but does not work for computed non-stored binary fields.

As a workaround, this module marks `avatar_128` `store=True`. In combination
with setting a lower value for images in the `Force Db For Default Attachment
Rules` FS Storage settings, this helps avoiding bloat in the `ir_attachment`
table.
