import Html
import numpy as np

class MMHtml:
    def __init__(self):
        return
            
    # TODO: Make another table for the system Ax=b
    # WriteHtml should be rewritten to just do dispatch, make a new top-level
    # The top level should take an array or dictionary of MM objects
    # and figure out what to do with them.

    def writeHtml(self, mmData, fn):
        h = Html.Html()
        dataHtml= h.html(h.head(h.matrixtablestyle() + h.title('Matrix data'))+h.body(self.renderHtmlData(h, mmData)))
        self.htmlfh= open(fn, mode='w')
        
        self.htmlfh.writelines(dataHtml)
        
    def renderHtmlData(self, h, mmData):
        if (isinstance(mmData, list)):
            dataHtml = ''
            for inst in mmData:
                dataHtml= dataHtml + h.td(self.renderHtmlData(h, inst))
            return h.table(h.tr(dataHtml))
        else:
            if (mmData.shape == 'coordinate'):
                dataHtml= self.renderHtmlMatrix(h, mmData)
            elif (mmData.shape == 'array'):
                dataHtml= self.renderHtmlArray(h, mmData)
            else:
                print "Unimplemented shape " + mmData.shape
        return dataHtml           

    def renderHtmlArray(self, h, mmData):
        dataTable= ''
        for j in range(0, mmData.entries-1):
            tableRow = h.td(str(mmData.fullArray[j]))
            tableRow= h.tr(tableRow) + "\n"
            dataTable= dataTable + tableRow
        dataTable= h.table(dataTable)
        return dataTable
        
    def renderHtmlMatrix(self, h, mmData):
        dataTable= ''
        for j in range(0, mmData.ysize-1):
            tableRow= ''
            for i in range(0, mmData.xsize-1):
                if (i == j):
                    tableRow += h.tdh(str(mmData.fullMatrix[j][i]))
                else:
                    tableRow += h.td(str(mmData.fullMatrix[j][i]))
            tableRow= h.tr(tableRow) + "\n"
            dataTable= dataTable + tableRow
        dataTable= h.table(dataTable)
        return dataTable
    
if __name__ == "__main__":
    
    import MatrixMarket as mm
    
    MMHtmlWriter= MMHtml()
    MMReaderRHS= mm.MatrixMarket()
    MMRHS= MMReaderRHS.read('mmRHS.mm') 
    
    MMReaderX= mm.MatrixMarket()
    MMX= MMReaderX.read('mmx.mm')     
    
    MMReaderMMA= mm.MatrixMarket()     
    MMA= MMReaderMMA.read('mmA.mm')
    MMHtmlWriter.writeHtml([MMA, MMX, MMRHS], 'mmA.html')
    