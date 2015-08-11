import types

def mixin(child, _super):
    '''The function of child overrides _super's, as normal inheritance'''
    assert type(_super) is types.ClassType

    if type(child) is types.ClassType and _super not in child.__bases__:
        child.__bases__ += (_super,)
    else:
        for name, value in _super.__dict__.items():
            if name[0] != '_' and name not in dir(child) and callable(value):
                if type(value) in [types.FunctionType, types.MethodType]:
                    setattr(child, name, types.MethodType(value, child))
                else:
                    setattr(child, name, value)

        for base in _super.__bases__:
            mixin(child, base)

