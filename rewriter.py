#rewrites text files

# ((?:\t?[._].*?\n)*)

#types of changes: [op-sub, op-condense, op-expand, del-nops, vac-ops, add-nops, cond-spaghetti, uncond-spaghetti]
import random
import re
import sys

class Rewriter():
	def __init__(_,changeVec=[1,1,1,1,1,1,1,1]):
		_.pEnd = ".cfi_endproc"
		_.pStart = ".cfi_startproc"
		_.regs = [r"%rbx", r"%rcx", r"%rdx", r"%rsi", r"%rdi"]
		_.ends = {_.pEnd,"call","callq","ret","retq","leave","loop","loope","loopne","loopnz","loopz",\
					"enter","js","jns","jnz","jz","jno","jo","jbe","jb","jle",\
					"jl","jae","ja","jge","jg","jne","je","jmp"}
		_.instPrefix = re.compile(r"^\t[a-z]")
		changes = ( (
					(re.compile(r"\tadd(l|b|q|\b)\t\$(\d+), (%[re].[ixp])\n",re.MULTILINE|re.DOTALL),
						(r"\tsub\1\t$-\2, \3\n",
						r"\txor\1\t$-\2, \3\n")
					),

					(re.compile(r"\ttest(l|b|q|\b)\t((?:%[re].[ixp])|(?:\$\d+)), (%[re].[ixp])\n",re.MULTILINE|re.DOTALL),
						(r"\tor\1\t\2, \3\n",)
					)

				),
		        (
					(re.compile(r"\tneg(?P<size>l|b|q|\b)\t(?P<reg1>%[re].[ixp])\n((?:\t?[\._][^\n]*?\n)*)\tsub(?P=size)\t(?P=reg1), (?P<reg2>%[re].[ixp])\n((?:\t?[\._][^\n]*?\n)*)\tneg(?P=size)\t(?P=reg2)\n",re.MULTILINE|re.DOTALL),
						(r"\tadd\1\t\2, \4\n\3\5",)
					),
					(re.compile(r"^\tpush(?P<name>l|b|q|\b)\t(%[re].[ixp])\n+((?:\t?[\._][^\n]*?\n)*)\tpop(?P=name)\t(%[re].[ixp])\n",re.MULTILINE|re.DOTALL),
						(r"mov\1\t\2, \4\n\3",)),

					(re.compile(r"\tpush(?P<name1>l|b|q|\b)\t((?:%[re].[ixp])|(?:\$\d+))\n+((?:\t?[\._][^\n]*?\n)*)\tpop(?P=name1)\t(%[re].[ixp])\n",re.MULTILINE|re.DOTALL),
						(r"\tmov\1\t\2, \4\n\3",)),

					(re.compile(r"\txor(?P<name2>l|b|q|\b)\t(?P<name3>%[re].[ixp]), (?P=name3)\n+((?:\t?[\._][^\n]*?\n)*)\tadd(?P=name2)\t((?:%[re].[ixp])|(?:\$\d+)), (?P=name3)\n",re.MULTILINE|re.DOTALL),
						(r"\tmov\1\t\4, \2\n\3",)),

					(re.compile(r"\tand(?P<n1>l|b|q|\b)\t\$0, (?P<n3>%[re].[ixp])\n((?:\t?[\._][^\n]*?\n)*)\tadd(?P=n1)\t((?:%[re].[ixp])|(?:\$\d+)), (?P=n3)\n",re.MULTILINE|re.DOTALL),
						(r"\tmov\1\t\4, \2\n\3",))

				),
		        (
					(re.compile(r"^\tmov(l|b|q|\b)\t((?:%[re].[ixp])|(?:\$\d+)), (%[re].[ixp])\n",re.MULTILINE|re.DOTALL),
						(r"\tpush\1\t\2\n\tpop\1\t\3\n",
						 r"\txor\1\t\3, \3\n\tadd\1\t\2, \3\n",
						 r"\tand\1\t$0, \3\n\tadd\1\t\2, \3\n")
					),
					(re.compile(r"\tadd(l|b|q|\b)\t(%[re].[ixp]), (%[re].[ixp])\n",re.MULTILINE|re.DOTALL),
						(r"\tneg\1\t\2\n\tsub\1\t\2, \3\n\tneg\1\t\2\n",)
					)
				),
		        (
					(re.compile(r"^\t(?:nop(?:;|\n\t))*?(?:nop)\n",re.MULTILINE|re.DOTALL),(r"\tnop\n","")),
				))
		actions = [_.getVacuousOps,_.getVacuousNops,_.makeCondJmp,_.makeUncJmp]
		_.changeTypes = [changes[i] for i in range(4) if changeVec[i]]
		_.extraChanges = [actions[i-4] for i in range(4,8) if changeVec[i]]
		_.extraChanges += [_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught,_.doNaught]
		if changeVec[6]:
			_.condTemplates = ("\tcmpq\t%s, %s\n\tje %s\n", #must be true
								"\ttestq\t%s, %s\n\tje %s\n", #must be false
								"\tcmpq\t$0, %s\n\tjne %s\n", #must be true
								"\ttestq\t$0, %s\n\tjne %s\n", #must be false
								)
		_.uncTemplate = "\tjmp\t%s\n"
		random.shuffle(_.extraChanges)


	def parseNrewrite(_,inFile,outFile):
		_.inf = open(inFile,"rU",errors="surrogateescape")
		_.ouf = open(outFile,"w")
		_.randLab = random.randint(100,200)
		_.writeTopMat(_.inf.readline())
		_.fname = inFile.split("/")[-1].replace(".","")
		endMat = list()
		curln = _.inf.readline()
		while curln.strip() != _.pEnd:
			(chnk,curln) = _.getChunk(curln)
			contRet = curln.strip() == _.pEnd
			new,end = _.getNewChunk(chnk,contRet)
			_.ouf.write(new+("\n" if contRet else "\n"+curln))
			endMat += end
			if not contRet:
				curln = _.inf.readline()
		if endMat:
			_.ouf.write(_.uncTemplate % (".L_"+str(_.randLab)+_.fname))
			for endStr in endMat:
				_.ouf.write(endStr)
			_.ouf.write(".L_"+str(_.randLab)+_.fname+":\n")
		_.ouf.write(curln)
		_.writeBotMat(_.inf.readline())

	def writeTopMat(_,ln):
		while ln.strip() != _.pStart:
			_.ouf.write(ln)
			ln = _.inf.readline()
		_.ouf.write(ln)

	def writeBotMat(_,ln):
		while ln:
			_.ouf.write(ln)
			ln = _.inf.readline()
		_.inf.close()
		_.ouf.close()
		print("Done, baby!")

	def getNewChunk(_,chnk,containsRet):
		random.shuffle(_.changeTypes)
		outstr = ""
		endlst = []
		i = 0
		l = len(_.changeTypes)
		while chnk and (i<l):
			ctype = _.changeTypes[i]
			j = 0
			jl = len(ctype)
			while (j < jl) and chnk:
				if chnk.strip().startswith("."):
					rem = chnk.split("\n")
					outstr += rem[0] + "\n"
					chnk = "\n".join(rem[1:])
				(ptrn,subs) = ctype[j]
				mtc = re.match(ptrn,chnk)
				if mtc and (random.random()<0.5):
					x = re.sub(mtc.re,random.choice(subs),mtc.group(0))
					outstr += x
					chnk = chnk[len(mtc.group(0)):]
					random.shuffle(_.changeTypes)
					j = jl
					i = 0
				else:
					j += 1
			i += 1
			if i == l:
				rem = chnk.split("\n")
				outstr += rem[0]+"\n"
				chnk = "\n".join(rem[1:])
				i = 0
		if chnk:
			outstr += chnk

		#Now for step 2 transformations...
		olist = outstr.split("\n")
		idx = 0
		l = (len(olist) -2 if containsRet else len(olist))
		while idx < l:
			(newCode,endCode,lsUsed) = random.choice(_.extraChanges)(olist,idx+1,l)
			olist[idx] += newCode
			endlst += endCode
			idx += lsUsed
		return ("\n".join([ln for ln in olist if ln]),endlst)

	def getChunk(_,ln):
		out = ''
		while (ln.strip() =='') or (ln.strip().split()[0] not in _.ends) :
			out += ln
			ln = _.inf.readline()
		return (out,ln)

	def makeCondJmp(_,lst,idx,l):
		if (l-idx) < 3:
			return ("",[],3)
		newLab1 = ".L_"+str(_.randLab)+_.fname
		endlst = [newLab1+":\n"]
		jOpt = random.randint(0,3)
		reg = random.choice(_.regs)
		if jOpt < 2:
			outstr = "\n"+_.condTemplates[jOpt] % (reg,reg,newLab1)
		else:
			outstr = "\n"+_.condTemplates[jOpt] % (reg,newLab1)
		lns = random.randint(2,7)
		newLab2 = ".L_"+str(_.randLab+1)+_.fname
		_.randLab += 2
		count = 0
		if jOpt % 2:  #AKA Jump needs nonsense
			while (count < lns) and (idx < l):
				endlst[0] += _.getVacuousOps(None,None,None)[0]+"\n"
				count += 1
				idx += 1
		else:
			while (count < lns) and (idx < l):
				s = lst[idx]
				endlst[0] += s+"\n"
				lst[idx] = ""
				count += 1
				idx += 1
		outstr += newLab2+":"
		endlst[0] += _.uncTemplate % newLab2
		return (outstr,endlst,count)

	def makeUncJmp(_,lst,idx,l):
		if (l-idx) < 3:
			return ("",[],3)
		newLab1 = ".L_"+str(_.randLab)+_.fname
		endlst = [newLab1+":\n"]

		lns = random.randint(2,7)
		newLab2 = ".L_"+str(_.randLab+1)+_.fname
		_.randLab += 2
		count = 0
		while (count < lns) and (idx < l):
			s = lst[idx]
			endlst[0] += s+"\n"
			lst[idx] = ""
			count += 1
			idx += 1
		outstr = "\n"+(_.uncTemplate % newLab1)+newLab2+":"
		endlst[0] += _.uncTemplate % newLab2
		return (outstr,endlst,count)

	def doNaught(_,lst,idx,l):
		return ("",[],1)

	def getVacuousOps(_,lst,idx,l):
		i = random.randint(1,7)
		reg = random.choice(_.regs)
		if i==1:
			out = "\n\tnotq\t"+reg+"\n\tnotq\t"+reg
		elif i==2:
			out = "\n\torq\t$0, "+reg
		elif i==3:
			out = "\n\tpushq\t"+reg+"\n\tpopq\t"+reg
		elif i==4:
			out = "\n\tdecq\t"+reg+"\n\tincq\t"+reg
		elif i==5:
			rint = str(random.randint(-100,100))
			out = "\n\taddq\t$"+rint+", "+reg+"\n\tsubq\t$"+rint+", "+reg
		elif i==6:
			out = "\n\tandq\t"+reg+", "+reg
		else:
			out = "\n\tmovq\t"+reg+", "+reg
		return (out,[],2)

	def getVacuousNops(_,lst,idx,l):
		return ("\n\t"+("; ".join(["nop"]*random.randint(2,4))),[],2)

if __name__ == "__main__":
	fname = sys.argv[1]
	oname = sys.argv[2]
	chngs = [int(x) for x in sys.argv[3].split(",")]
	k = Rewriter(chngs)
	k.parseNrewrite(fname,oname)
	with open(oname, "r") as cleanupFile:
		readFile = cleanupFile.read()
		readFile = re.sub(r"\n.?\n", "\n", readFile) 
		readFile = re.sub(r"\n[^\s]\t","\n\t",readFile)
	with open(oname, "w") as fixedFile:
		fixedFile.write(readFile)
