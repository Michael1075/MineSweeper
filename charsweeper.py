print('Let\'s begin our mine-searching!')

#Part 1: prepare the empty map
import math
import random
#marks
null='o'
blank='_'
flag='+'
mine=' '
seperator='-'*30
x=16
y=30
z=99
print('We have {2} mines in the following {0}-by-{1} table. Good luck!'.format(str(x),str(y),str(z)))
wholemap=[]
for i in range(1,x+1,1):
    for j in range(1,y+1,1):
        p=i,j
        wholemap.append(p)
        
def nbhood(i,j):
    circle=[(i-1,j-1),(i-1,j),(i-1,j+1),(i,j-1),(i,j+1),(i+1,j-1),(i+1,j),(i+1,j+1)]
    surround=list(set(circle).intersection(set(wholemap)))
    return surround
    
#Part 2: print the empty game map
gamemap={}
for i in range(1,x+1,1):
    for j in range(1,y+1,1):
        p=i,j
        gamemap[p]=null
        
def createmap(dictionary):
    value=list(dictionary.values())
    for k in range(1,x+1,1):
        line=value[y*(k-1):y*k:1]
        result=' '.join(line)
        print(result)

createmap(gamemap)
print(seperator)

#Part 3: the first guess
i=random.randint(1,x)
j=random.randint(1,y)
firstguess=i,j
print('Step 1 :',firstguess)
print('Remaining mines :',z,' Method : - ')
square=[(i-1,j-1),(i-1,j),(i-1,j+1),(i,j-1),(i,j),(i,j+1),(i+1,j-1),(i+1,j),(i+1,j+1)]
rest=list(set(wholemap).difference(set(square)))
allmines=random.sample(rest,z)

def nbmine(i,j):
    surround=nbhood(i,j)
    nbmines=list(set(allmines).intersection(set(surround)))
    return nbmines
    
#Part 4: make the key map, which is based on mines
keymap={}
for i in range(1,x+1,1):
    for j in range(1,y+1,1):
        p=i,j
        if p in allmines:
            keymap[p]=mine
        else:
            nbmines=nbmine(i,j)
            number=len(nbmines)
            if number==0:
                keymap[p]=blank
            else:
                keymap[p]=str(number)

#Part 5: extend the blank of the first guess

def extendmap(i,j,area):
    region=[]
    region.append((i,j))
    for p in region:
        surround=nbhood(p[0],p[1])
        for p in surround:
            if p in area and not p in region:
                region.append(p)
    return region

blanks=[]
for p in wholemap:
    if keymap[p]==blank:
        blanks.append(p)
region=extendmap(firstguess[0],firstguess[1],blanks)

for p in region:
    gamemap[p]=keymap[p]
    surround=nbhood(p[0],p[1])
    for p in surround:
        gamemap[p]=keymap[p]

createmap(gamemap)
print(seperator)


#Part 6: play
for step in range(2,x*y,1):
    
    #Part 7: define functions
    recentnulls=[]
    recentblanks=[]
    recentflags=[]
    recentnumbers=[]
    for p in wholemap:
        if gamemap[p]==null:
            recentnulls.append(p)
        elif gamemap[p]==blank:
            recentblanks.append(p)
        elif gamemap[p]==flag:
            recentflags.append(p)
        else:
            recentnumbers.append(p)
    
    def nbnull(i,j):
        surround=nbhood(i,j)
        nbnulls=list(set(recentnulls).intersection(set(surround)))
        return nbnulls
    def nbblank(i,j):
        surround=nbhood(i,j)
        nbblanks=list(set(recentblanks).intersection(set(surround)))
        return nbblanks
    def nbflag(i,j):
        surround=nbhood(i,j)
        nbflags=list(set(recentflags).intersection(set(surround)))
        return nbflags
    def nbnumber(i,j):
        surround=nbhood(i,j)
        nbnumbers=list(set(recentnumbers).intersection(set(surround)))
        return nbnumbers
        
    valuablenumbers=[]
    for p in recentnumbers:
        nbnulls=nbnull(p[0],p[1])
        if len(nbnulls)!=0:
            valuablenumbers.append(p)
    
    valuablenumberpairs=[]
    for p in valuablenumbers:
        for q in valuablenumbers:
            valuablenumberpairs.append((p,q))
    
    restmines=list(set(allmines).difference(set(recentflags)))
    
    if len(recentnulls)==len(restmines) or len(recentnulls)==0:
        print('Congratulations! You\'ve won the game!')
        for p in allmines:
            gamemap[p]=flag
        createmap(gamemap)
        break
        
    #Part 8: decide the next step
    #If mode=0, a box will be opened. If mode=1, a flag will be put.
    
    countone=1
    counttwo=1
    countthree=1
    
    if len(valuablenumbers)==0:
        if len(restmines)==len(recentnulls):
            mode=1
            method='-'
        elif len(restmines)==0:
            mode=0
            method='-'
        else:
            mode=0
            method=4
            bestprobability=len(restmines)/len(recentnulls)
        k=random.sample(recentnulls,1)
        p=k[0]
        i=p[0]
        j=p[1]
        
    else:
        #method 1
        for p in valuablenumbers:
            nbnulls=nbnull(p[0],p[1])
            nbflags=nbflag(p[0],p[1])
            if int(gamemap[p])==len(nbnulls)+len(nbflags):
                mode=1
                k=random.sample(nbnulls,1)
                p=k[0]
                i=p[0]
                j=p[1]
                method=1
                break
            else:
                if countone==len(valuablenumbers):
                    
                    #method 2
                    for p in valuablenumbers:
                        nbnulls=nbnull(p[0],p[1])
                        nbflags=nbflag(p[0],p[1])
                        if int(gamemap[p])==len(nbflags):
                            mode=0
                            k=random.sample(nbnulls,1)
                            p=k[0]
                            i=p[0]
                            j=p[1]
                            method=2
                            break
                        else:
                            if counttwo==len(valuablenumbers):
                                
                                #method 3
                                for p,q in valuablenumberpairs:
                                        
                                    pnbnulls=nbnull(p[0],p[1])
                                    qnbnulls=nbnull(q[0],q[1])
                                    commonnulls=list(set(pnbnulls).intersection(set(qnbnulls)))
                                    pselfnbnulls=list(set(pnbnulls).difference(set(commonnulls)))
                                    qselfnbnulls=list(set(qnbnulls).difference(set(commonnulls)))
                                    selfnulls=list(set(pselfnbnulls).union(set(qselfnbnulls)))
                                        
                                    pnbflags=nbflag(p[0],p[1])
                                    qnbflags=nbflag(q[0],q[1])
                                    commonflags=list(set(pnbflags).intersection(set(qnbflags)))
                                    pselfnbflags=list(set(pnbflags).difference(set(commonflags)))
                                    qselfnbflags=list(set(qnbflags).difference(set(commonflags)))
                                        
                                    if len(commonnulls)!=0 and len(selfnulls)!=0 and p!=q and int(gamemap[p])-int(gamemap[q])==len(pselfnbnulls)+len(pselfnbflags)-len(qselfnbflags):
                                        k=random.sample(selfnulls,1)
                                        p=k[0]
                                        i=p[0]
                                        j=p[1]
                                        if p in pselfnbnulls:
                                            mode=1
                                        else:
                                            mode=0
                                        method=3
                                        break
                                                
                                    else:
                                        if countthree==len(valuablenumbers)**2:
                                                    
                                            #method 4
                                            edge=[]
                                            for p in valuablenumbers:
                                                nbnulls=nbnull(p[0],p[1])
                                                for p in nbnulls:
                                                    if not p in edge:
                                                        edge.append(p)
                                            restnulls=list(set(recentnulls).difference(set(edge)))
                                            
                                            orders=[]
                                            correctorders=[]
                                            for k in range(2**len(edge),2**(len(edge)+1),1):
                                                experiment=gamemap.copy()
                                                order=bin(k)
                                                orders.append(order)
                                                correct=0
                                                for queue in range(3,len(edge)+3,1):
                                                    if int(order[queue])==1:
                                                        experiment[edge[queue-3]]=flag
                                                experimentflags=[]
                                                for p in wholemap:
                                                    if experiment[p]==flag:
                                                        experimentflags.append(p)
                                                        
                                                def expnbflag(i,j):
                                                    surround=nbhood(i,j)
                                                    expnbflags=list(set(experimentflags).intersection(set(surround)))
                                                    return expnbflags
                                                for p in valuablenumbers:
                                                    expnbflags=expnbflag(p[0],p[1])
                                                    if int(experiment[p])!=len(expnbflags):
                                                        correct=correct+1
                                                if correct==0:
                                                    correctorders.append(order)
                                                for order in correctorders:
                                                    if len(experimentflags)>len(restmines) or len(experimentflags)+len(restnulls)<len(restmines):
                                                        correctorders.remove(order)
                                                    
                                            probabilities={}
                                            
                                            allfrequencies=0
                                            for queue in range(3,len(edge)+3,1):
                                                frequency=0
                                                for order in correctorders:
                                                    frequency=frequency+int(order[queue])
                                                allfrequencies=allfrequencies+frequency
                                                probability=frequency/len(correctorders)
                                                probabilities[edge[queue-3]]=probability
                                            
                                            if len(restnulls)!=0:
                                                eigenprobability=((len(correctorders)*len(restmines)-allfrequencies)/(len(correctorders)*len(restnulls)))
                                                for p in restnulls:
                                                    probabilities[p]=eigenprobability
                                            
                                            bestchoices=[]
                                            if max(set(probabilities.values()))==1:
                                                for p in recentnulls:
                                                    if probabilities[p]==1:
                                                        bestchoices.append(p)
                                                mode=1
                                            else:
                                                bestprobability=min(set(probabilities.values()))
                                                for p in recentnulls:
                                                    if probabilities[p]==bestprobability:
                                                        bestchoices.append(p)
                                                mode=0
                                            k=random.sample(bestchoices,1)
                                            p=k[0]
                                            i=p[0]
                                            j=p[1]
                                            method=4
                                            break
                                                    
                                        else:
                                            countthree=countthree+1
                            else:
                                counttwo=counttwo+1
                else:
                    countone=countone+1
                    
    #Part 9: run the step
    if mode==0:
        p=i,j
        print('Step',step,':',p)
        if method==4:
            print('Remaining mines :',len(restmines),' Method :',method,' Probability of safety: {}%%'.format(round(100*(1-bestprobability),2)))
        else:
            print('Remaining mines :',len(restmines),' Method :',method)
            
        if keymap[p]==mine:
            openarea=list(set(recentblanks).union(set(list(set(recentflags).union(set(recentnumbers))))))
            percentage=len(openarea)/(x*y)*100
            for p in restmines:
                gamemap[p]=mine
            createmap(gamemap)
            print(seperator)
            print('Ooops! You\'ve lost the game! Only %s to go.'%len(restmines))
            print('You\'ve already opened {}%% of the table.'.format(round(percentage,2)))
            break
        elif keymap[p]==blank:
            region=extendmap(p[0],p[1],blanks)
            for p in region:
                gamemap[p]=keymap[p]
                surround=nbhood(p[0],p[1])
                for p in surround:
                    gamemap[p]=keymap[p]
        else:
            gamemap[p]=keymap[p]
            
        createmap(gamemap)
        print(seperator)
    
    else:
        p=i,j
        print('Step',step,':',p,'(flag here)')
        print('Remaining mines :',len(restmines)-1,' Method :',method)
        gamemap[p]=flag
        createmap(gamemap)

        print(seperator)