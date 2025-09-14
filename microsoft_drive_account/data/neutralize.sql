-- neutralization of Microsoft drive
UPDATE res_users
    SET microsoft_drive_token = NULL,
        microsoft_drive_rtoken = NULL,
        microsoft_drive_status='not_connected',
        microsoft_drive_token_validity = NULL;
