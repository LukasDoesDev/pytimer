import timeit


setup = "list1 = ['a', 'b'] ; list2 = ['a', 'b', 'c', 'd']"

mycode1 = '''
def myfn1(mylist, myotherlist):
    if len(mylist) == 1:
        return mylist[0] in myotherlist
    return myfn1(mylist[1:], myotherlist)
myfn1(list1, list2)
'''

mycode2 = '''
def myfn2(mylist, myotherlist):
    return all(elem in myotherlist for elem in mylist)
myfn2(list1, list2)
'''

print(timeit.timeit(setup=setup,
                    stmt=mycode1,
                    number=10000))

print(timeit.timeit(setup=setup,
                    stmt=mycode2,
                    number=10000))
