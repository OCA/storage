from . import models


def _precompute_avatar_128(env):
    # Get all columns from ir_attachment except id and res_field.
    env.cr.execute(
        """
        select string_agg(quote_ident(column_name), ', ')
        from information_schema.columns
        where table_schema = current_schema()
          and table_name = 'ir_attachment'
          and column_name not in ('id', 'res_field')
        """
    )
    cols = env.cr.fetchone()[0]
    # Duplicate all image_128 attachments as avatar_128 attachments unless
    # a corresponding avatar_128 attachment already exists.
    env.cr.execute(
        f"""
        insert into ir_attachment
            ({cols}, res_field)
        select
            {cols}, 'avatar_128'
        from
            ir_attachment ia1
        where
            res_field = 'image_128'
            and not exists (
                select
                    id
                from
                    ir_attachment
                where
                    res_field = 'avatar_128'
                    and res_model = ia1.res_model
                    and res_id = ia1.res_id
            )
        """
    )
