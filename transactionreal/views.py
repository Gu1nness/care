# Create your views here.
from base.views import BaseView
from transactionreal.forms import NewRealTransactionForm, EditRealTransactionForm
from transactionreal.models import TransactionReal
from userprofile.models import UserProfile

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.views.generic.edit import FormView

from itertools import chain

import logging
logger = logging.getLogger(__name__)


class MyRealTransactionView(BaseView):
  template_name = "transactionreal/mytransactionsreal.html"
  context_object_name = "my real transactions"
  
  def getActiveMenu(self):
    return 'transactions'
  
  def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
    context = super(MyRealTransactionView, self).get_context_data(**kwargs)
    userProfile = UserProfile.objects.get(user=self.request.user)
     
    sentTransactions = TransactionReal.getSentTransactionsReal(userProfile.id)
    receivedTransactions = TransactionReal.getReceivedTransactionsReal(userProfile.id)
    transactionsRealAll = list(chain(sentTransactions, receivedTransactions))
    transactionsRealAllSorted = sorted(transactionsRealAll, key=lambda instance: instance.date, reverse=True)
    
    if int(context['tableView']) == 0:
      context['tableView'] = False
    
    context['transactionsRealAll'] = transactionsRealAllSorted
    return context# Create your views here.


class SelectGroupRealTransactionView(BaseView):
  template_name = "transactionreal/newselectgroup.html"
  context_object_name = "select transaction group"
  
  def get_context_data(self, **kwargs):    
    context = super(SelectGroupRealTransactionView, self).get_context_data(**kwargs)
    userProfile = UserProfile.objects.get(user=self.request.user)
    groupaccounts = userProfile.groupAccounts.all
    context['groupaccounts'] = groupaccounts
    context['transactionssection'] = True
    return context


class NewRealTransactionView(FormView, BaseView):
  template_name = 'transactionreal/new.html'
  form_class = NewRealTransactionForm
  success_url = '/transactionreal/new/success/'
  
  def getActiveMenu(self):
    return 'transactions'
   
  def getGroupAccountId(self):
    if 'groupAccountId' in self.kwargs:
      return self.kwargs['groupAccountId']
    else:
      logger.debug(self.request.user.id)
      user = UserProfile.objects.get(user=self.request.user)
      if user.groupAccounts.count():
        return user.groupAccounts.all()[0].id
      else:
        return 0
    
  def get_form(self, form_class):
    logger.debug('get_form()')
    return NewRealTransactionForm(self.getGroupAccountId(), self.request.user, **self.get_form_kwargs())   
    
  def form_valid(self, form):
    logger.debug('form_valid()')
    super(NewRealTransactionView, self).form_valid(form)
    form.save()
    return HttpResponseRedirect( '/')
  
  def form_invalid(self, form):
    logger.debug('form_invalid()')
    groupAccount = form.cleaned_data['groupAccount']  
    super(NewRealTransactionView, self).form_invalid(form)
    return HttpResponseRedirect( '/transactionsreal/new/' + str(groupAccount.id))
    
  def get_context_data(self, **kwargs):
    logger.debug('NewRealTransactionView::get_context_data() - groupAccountId: ' + str(self.getGroupAccountId()))
    context = super(NewRealTransactionView, self).get_context_data(**kwargs)
    
    if (self.getGroupAccountId()):
      form = NewRealTransactionForm(self.getGroupAccountId(), self.request.user)
      context['form'] = form
      context['nogroup'] = False
    else:
      context['nogroup'] = True
    return context


class EditRealTransactionView(FormView, BaseView):
  template_name = 'transactionreal/edit.html'
  form_class = EditRealTransactionForm
  success_url = '/transactionsreal/0'
  
  def getActiveMenu(self):
    return 'shares'
   
  def get_form(self, form_class):
    pk = self.kwargs['pk']
    transaction = TransactionReal.objects.get(pk=pk)
    return EditRealTransactionForm(self.kwargs['pk'], self.request.user, instance=transaction, **self.get_form_kwargs())   

  def form_valid(self, form):
    logger.debug('EditRealTransactionView::form_valid()')
    super(EditRealTransactionView, self).form_valid(form)
    transaction = TransactionReal.objects.get(pk=self.kwargs['pk'])
    if self.request.user == transaction.sender.user:
      form.save()
    return HttpResponseRedirect( '/transactionsreal/0' )
  
  def get_context_data(self, **kwargs):
    context = super(EditRealTransactionView, self).get_context_data(**kwargs)
    transaction = TransactionReal.objects.get(pk=self.kwargs['pk'])
    
    if self.request.user == transaction.sender.user:
      form = EditRealTransactionForm(self.kwargs['pk'], self.request.user, instance=transaction, **self.get_form_kwargs())
      context['form'] = form
    
    return context

