Login
=====

Miscellaneous information related to logging in to CastleCMS

Password Complexity
-------------------

- Minimum password length of 8 characters is *actually* enforced

- pwexpiry allows setting password expiration dates

- pwexpiry allows preventing use of the last X passwords used by a user

- Users can be added to a whitelist for pwexpiry features

Security
--------

- Users that need to change their password are not logged in until they have done so

- The change password screen of the login form checks if the inputted password is valid
  according to CastleCMS's password complexity settings

- The change password screen also respects any other PAS restrictions
