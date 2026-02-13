from workos.types.sso.profile import ProfileAndToken

with open('workos_attrs.txt', 'w') as f:
    f.write('\n'.join(dir(ProfileAndToken)))
