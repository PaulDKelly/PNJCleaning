from workos.types.sso.profile import Profile

with open('workos_profile_attrs.txt', 'w') as f:
    f.write('\n'.join(dir(Profile)))
