"""Cursos do CCT e suas matrizes de referência; CAR não é um curso."""

COURSES = (
    dict(key='mc', id='matematica-computacional', prefix='matcomp', title='Matemática Computacional', matrix='Matemática Computacional'),
    dict(key='cc', id='ciencia-computacao', prefix='computacao', title='Ciência da Computação', matrix='Ciência da Computação (CC002)', legacy='Ciência da Computação (CC001)'),
    dict(key='civil', id='engenharia-civil', prefix='civil', title='Engenharia Civil', matrix='Engenharia Civil'),
    dict(key='materiais', id='engenharia-materiais', prefix='materiais', title='Engenharia de Materiais', matrix='Engenharia de Materiais'),
    dict(key='software', id='engenharia-software', prefix='software', title='Engenharia de Software', matrix='Engenharia de Software'),
)


def curriculum(definitions, course):
    """A matriz atual prevalece; a anterior acrescenta apenas códigos exclusivos."""
    required = set(definitions[course['matrix']][2].split())
    optional = set(definitions[course['matrix']][1].split())
    if course.get('legacy'):
        current = required | optional
        required |= set(definitions[course['legacy']][2].split()) - current
        optional |= set(definitions[course['legacy']][1].split()) - current
    return required, optional
